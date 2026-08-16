"""
Business logic for submitting an application and running it through the
full ML pipeline (predict -> SHAP -> LIME -> counterfactual), persisting
every step so it can be re-fetched without recomputation later.
"""

from app.extensions import db
from app.models import Applicant, Application, Prediction, Explanation, Counterfactual
from app.services import ml_service


def get_or_create_applicant(user) -> Applicant:
    applicant = Applicant.query.filter_by(user_id=user.id).first()
    if not applicant:
        applicant = Applicant(user_id=user.id, full_name=user.full_name)
        db.session.add(applicant)
        db.session.commit()
    return applicant


def submit_application(user, features: dict) -> dict:
    applicant = get_or_create_applicant(user)

    application = Application(applicant_id=applicant.id)
    application.set_features(features)
    db.session.add(application)
    db.session.flush()
    application.public_id = f"APP-{application.created_at.year if application.created_at else __import__('datetime').datetime.utcnow().year}-{application.id:04d}"
    db.session.commit()

    # 1. Prediction
    result = ml_service.predict_application(features)
    metadata = ml_service.get_model_metadata()
    prediction = Prediction(
        application_id=application.id,
        decision=result["prediction"],
        probability=result["probability"],
        model_name=metadata.get("final_model", "unknown"),
    )
    db.session.add(prediction)
    db.session.commit()

    # 2. SHAP explanation
    shap_result = ml_service.get_shap_explanation(features, result["prediction"], result["probability"])
    shap_explanation = Explanation(prediction_id=prediction.id, method="shap")
    shap_explanation.set_contributions(shap_result["contributions"])
    shap_explanation.plain_english = shap_result["plain_english"]
    db.session.add(shap_explanation)

    # 3. LIME explanation
    lime_result = ml_service.get_lime_explanation(features, result["prediction"], result["probability"])
    lime_explanation = Explanation(prediction_id=prediction.id, method="lime")
    lime_explanation.set_contributions(lime_result["contributions"])
    lime_explanation.plain_english = lime_result["plain_english"]
    db.session.add(lime_explanation)

    # 4. Counterfactual (only meaningful for rejections, but always attempted)
    cf_result = ml_service.get_counterfactual(features)
    counterfactual = Counterfactual(prediction_id=prediction.id, found=cf_result["found"], message=cf_result["message"])
    counterfactual.set_alternatives(cf_result["alternatives"])
    db.session.add(counterfactual)

    db.session.commit()

    return {
        "application": application.to_dict(),
        "prediction": prediction.to_dict(),
        "shap": shap_explanation.to_dict(),
        "lime": lime_explanation.to_dict(),
        "comparison": ml_service.get_shap_lime_comparison(shap_result["contributions"], lime_result["contributions"]),
        "counterfactual": counterfactual.to_dict(),
    }


def get_applications_for_user(user) -> list:
    applicant = Applicant.query.filter_by(user_id=user.id).first()
    if not applicant:
        return []
    return [app.to_dict() | {"prediction": app.prediction.to_dict() if app.prediction else None}
            for app in applicant.applications]


def get_application_detail(application_id: int, user) -> dict | None:
    application = Application.query.get(application_id)
    if not application:
        return None

    # Applicants may only view their own applications; staff may view any.
    if user.role == "applicant" and application.applicant.user_id != user.id:
        return None

    prediction = application.prediction
    if not prediction:
        return {"application": application.to_dict(), "prediction": None}

    explanations = {e.method: e.to_dict() for e in prediction.explanations}
    counterfactual = prediction.counterfactuals[0].to_dict() if prediction.counterfactuals else None

    comparison = None
    if "shap" in explanations and "lime" in explanations:
        comparison = ml_service.get_shap_lime_comparison(
            explanations["shap"]["contributions"], explanations["lime"]["contributions"]
        )

    return {
        "application": application.to_dict(),
        "prediction": prediction.to_dict(),
        "shap": explanations.get("shap"),
        "lime": explanations.get("lime"),
        "comparison": comparison,
        "counterfactual": counterfactual,
    }


def get_all_applications() -> list:
    """Staff/admin view of every application, for the analytics dashboard."""
    return [
        app.to_dict() | {"prediction": app.prediction.to_dict() if app.prediction else None}
        for app in Application.query.order_by(Application.created_at.desc()).all()
    ]
