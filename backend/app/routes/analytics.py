from collections import Counter
from flask import Blueprint, g, jsonify

from app.middleware.auth_middleware import roles_required
from app.services import ml_service, application_service
from app.services.ml_service import MLServiceError

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.get("/analytics/model")
@roles_required("loan_officer", "admin")
def model_analytics():
    try:
        metadata = ml_service.get_model_metadata()
    except MLServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    return jsonify(metadata), 200


@analytics_bp.get("/analytics/shap")
@roles_required("loan_officer", "admin")
def global_shap():
    try:
        importance = ml_service.get_global_shap()
    except MLServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    return jsonify({"global_importance": importance}), 200


@analytics_bp.get("/analytics/applications-summary")
@roles_required("loan_officer", "admin")
def applications_summary():
    applications = application_service.get_all_applications()
    total = len(applications)
    approved = sum(1 for a in applications if a.get("prediction") and a["prediction"]["decision"] == "APPROVED")
    rejected = sum(1 for a in applications if a.get("prediction") and a["prediction"]["decision"] == "REJECTED")
    return jsonify({
        "total": total,
        "approved": approved,
        "rejected": rejected,
        "approval_rate": round(approved / total, 4) if total else None,
    }), 200


@analytics_bp.get("/dashboard/stats")
@roles_required("applicant", "loan_officer", "admin")
def dashboard_stats():
    applications = (application_service.get_applications_for_user(g.current_user)
                    if g.current_user.role == "applicant" else application_service.get_all_applications())
    decisions = Counter(a["prediction"]["decision"] for a in applications if a.get("prediction"))
    risks = Counter(a["prediction"].get("risk_level", "MEDIUM") for a in applications if a.get("prediction"))
    return jsonify({
        "total": len(applications),
        "approved": decisions["APPROVED"],
        "rejected": decisions["REJECTED"],
        "under_review": sum(1 for a in applications if not a.get("prediction")),
        "approval_rate": round(decisions["APPROVED"] / len(applications) * 100, 1) if applications else None,
        "risk_distribution": {"low": risks["LOW"], "medium": risks["MEDIUM"], "high": risks["HIGH"]},
        "recent_applications": applications[:5],
    }), 200
