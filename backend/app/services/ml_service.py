"""
Bridges the Flask backend to the ml/ package (prediction, SHAP, LIME,
counterfactuals, fairness). This is the ONLY place that touches the ml/
package directly -- routes call this service, never ml/ modules directly
(spec section 34: routes -> services -> ML/DB, not all-in-one routes).
"""

import os
import sys
from functools import lru_cache

_ML_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml"))

_ML_READY = False


class MLServiceError(Exception):
    def __init__(self, message: str, status_code: int = 503):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _require_ml() -> None:
    """Load heavy ML dependencies only when an ML endpoint is called.

    Authentication and account endpoints must remain usable on a fresh
    developer setup, even before optional ML packages and model assets are
    installed.  ML endpoints return a helpful 503 until that setup is done.
    """
    global _ML_READY, pd, ml_predict, load_pipeline, load_metadata, ModelNotTrainedError
    global local_shap_explanation, global_shap_importance, local_lime_explanation
    global generate_summary, compare_explanations, generate_counterfactual
    global run_fairness_analysis, RAW_DATA_FILE, model_value_to_indian_display
    global predict_transaction, load_transaction_pipeline, load_transaction_reference, TransactionModelNotTrainedError

    if _ML_READY:
        return
    try:
        import pandas as pd_module

        if _ML_ROOT not in sys.path:
            sys.path.insert(0, _ML_ROOT)
        from prediction.predictor import predict as predict_module, load_pipeline as pipeline_loader, load_metadata as metadata_loader, ModelNotTrainedError as not_trained_error
        from prediction.transaction_predictor import (predict_transaction as transaction_predictor,
                                   load_transaction_pipeline as transaction_pipeline_loader,
                                   load_transaction_reference as transaction_reference_loader,
                                   TransactionModelNotTrainedError as transaction_not_trained_error)
        from explainability.shap_explainer import local_shap_explanation as shap_local, global_shap_importance as shap_global
        from explainability.lime_explainer import local_lime_explanation as lime_local
        from explainability.explanation_engine import generate_summary as summary_generator
        from explainability.comparison import compare_explanations as explanation_comparer
        from counterfactual.dice_explainer import generate_counterfactual as counterfactual_generator
        from fairness.fairness_analyzer import run_fairness_analysis as fairness_runner
        from config import RAW_DATA_FILE as raw_data_file
        from app.services.indian_feature_mapper import model_value_to_indian_display as display_value
    except ImportError as error:
        raise MLServiceError(
            "ML dependencies are not installed. Run `pip install -r backend/requirements.txt` to enable predictions and explanations."
        ) from error

    pd = pd_module
    ml_predict, load_pipeline, load_metadata = predict_module, pipeline_loader, metadata_loader
    ModelNotTrainedError = not_trained_error
    predict_transaction = transaction_predictor
    load_transaction_pipeline = transaction_pipeline_loader
    load_transaction_reference = transaction_reference_loader
    TransactionModelNotTrainedError = transaction_not_trained_error
    local_shap_explanation, global_shap_importance = shap_local, shap_global
    local_lime_explanation, generate_summary = lime_local, summary_generator
    compare_explanations, generate_counterfactual = explanation_comparer, counterfactual_generator
    run_fairness_analysis, RAW_DATA_FILE = fairness_runner, raw_data_file
    model_value_to_indian_display = display_value
    _ML_READY = True


@lru_cache(maxsize=1)
def _reference_data():
    """A cached sample of real training data used as SHAP/LIME/DiCE background."""
    if not os.path.exists(RAW_DATA_FILE):
        raise MLServiceError(
            "Reference dataset not found. Run `python data/download_dataset.py` "
            "inside ml/ (requires internet) before using explainability features."
        )
    return pd.read_csv(RAW_DATA_FILE)


def _applicant_df(applicant: dict):
    _require_ml()
    from prediction.predictor import applicant_to_dataframe
    return applicant_to_dataframe(applicant)


def predict_application(applicant: dict) -> dict:
    _require_ml()
    try:
        return ml_predict(applicant)
    except ModelNotTrainedError as e:
        raise MLServiceError(str(e), 503)


def get_shap_explanation(applicant: dict, prediction: str, probability: float) -> dict:
    _require_ml()
    try:
        pipeline = load_pipeline()
        contributions = local_shap_explanation(pipeline, _applicant_df(applicant), _reference_data())
        summary = generate_summary([{**item, "value": model_value_to_indian_display(item["feature"], item["value"])} for item in contributions], prediction, probability)
        return {"contributions": contributions, "plain_english": summary}
    except ModelNotTrainedError as e:
        raise MLServiceError(str(e), 503)


def get_lime_explanation(applicant: dict, prediction: str, probability: float) -> dict:
    _require_ml()
    try:
        pipeline = load_pipeline()
        contributions = local_lime_explanation(pipeline, _applicant_df(applicant), _reference_data())
        summary = generate_summary([{**item, "value": model_value_to_indian_display(item["feature"], item["value"])} for item in contributions], prediction, probability)
        return {"contributions": contributions, "plain_english": summary}
    except ModelNotTrainedError as e:
        raise MLServiceError(str(e), 503)


def get_shap_lime_comparison(shap_contributions: list, lime_contributions: list) -> dict:
    _require_ml()
    return compare_explanations(shap_contributions, lime_contributions)


def get_counterfactual(applicant: dict) -> dict:
    _require_ml()
    try:
        pipeline = load_pipeline()
        return generate_counterfactual(pipeline, _applicant_df(applicant), _reference_data())
    except ModelNotTrainedError as e:
        raise MLServiceError(str(e), 503)


def get_global_shap() -> list:
    _require_ml()
    try:
        pipeline = load_pipeline()
        return global_shap_importance(pipeline, _reference_data())
    except ModelNotTrainedError as e:
        raise MLServiceError(str(e), 503)


def get_model_metadata() -> dict:
    _require_ml()
    try:
        return load_metadata()
    except ModelNotTrainedError as e:
        raise MLServiceError(str(e), 503)


def get_fairness_report() -> dict:
    _require_ml()
    try:
        return run_fairness_analysis()
    except FileNotFoundError as e:
        raise MLServiceError(str(e), 503)


def assess_merchant(features: dict) -> dict:
    _require_ml()
    try:
        from app.models import MerchantDocumentVerification
        from data.synthetic_transactions import TRANSACTION_FEATURES, TRANSACTION_LABELS, TRANSACTION_RANGES
        from fraud.pattern_detector import FRAUD_SCORE_THRESHOLD, detect_fraud_signals
        from prediction.transaction_predictor import transaction_to_dataframe

        errors = []
        for feature in TRANSACTION_FEATURES:
            if feature not in features or features[feature] in (None, ""):
                errors.append(f"'{feature}' is required.")
                continue
            try:
                features[feature] = float(features[feature])
            except (TypeError, ValueError):
                errors.append(f"'{feature}' must be a number.")
                continue
            minimum, maximum = TRANSACTION_RANGES[feature]
            if not minimum <= features[feature] <= maximum:
                errors.append(f"'{feature}' must be between {minimum} and {maximum}.")
        if errors:
            raise MLServiceError("Invalid transaction features: " + " ".join(errors), 400)

        result = predict_transaction(features)
        pipeline = load_transaction_pipeline()
        applicant_df = transaction_to_dataframe(features)
        reference_df = load_transaction_reference()
        labels = lambda feature: TRANSACTION_LABELS[feature]
        contributions = local_shap_explanation(
            pipeline, applicant_df, reference_df,
            feature_columns=TRANSACTION_FEATURES, label_for_fn=labels,
        )
        summary = generate_summary(
            contributions, result["prediction"], result["probability"],
            positive_direction="toward higher risk", negative_direction="toward lower risk",
            positive_prediction="HIGH_RISK",
        )
        fraud_result = None
        transaction_history = features.get("transaction_history")
        if transaction_history is not None:
            fraud_result = detect_fraud_signals(transaction_history)
            if fraud_result["fraud_score"] >= FRAUD_SCORE_THRESHOLD:
                summary += "\n- Transparent fraud-pattern rules also flagged abnormal transaction behavior; review the flagged days before relying on this risk assessment."
        verification = MerchantDocumentVerification.query.filter_by(merchant_id=str(features.get("merchant_id", ""))).first()
        verification_result = verification.to_dict() if verification else None
        if verification and not verification.consistent:
            summary += "\n- Persisted document consistency checks flagged a declaration mismatch; treat this as an additional risk signal."
        risk_signals = []
        if verification and not verification.consistent:
            risk_signals.append("document_consistency_mismatch")
        if fraud_result and fraud_result["fraud_score"] >= FRAUD_SCORE_THRESHOLD:
            risk_signals.append("fraud_pattern_warning")
        return {
            "prediction": {
                **result,
                "risk_score": round(result["probability"] * 100),
                "risk_level": "HIGH" if result["probability"] >= 0.66 else "MEDIUM" if result["probability"] >= 0.33 else "LOW",
                "model_name": "synthetic_transaction_model",
            },
            "shap": {"contributions": contributions, "plain_english": summary},
            "fraud": fraud_result,
            "document_verification": verification_result,
            "risk_signals": risk_signals,
            "disclaimer": "This assessment uses synthetic transaction data for demo purposes, not real Razorpay merchant data or policy.",
        }
    except TransactionModelNotTrainedError as e:
        raise MLServiceError(str(e), 503)


def check_merchant_fraud(merchant_id: str, transaction_history: list[dict]) -> dict:
    _require_ml()
    if not merchant_id:
        raise MLServiceError("'merchant_id' is required.", 400)
    if not isinstance(transaction_history, list) or not transaction_history:
        raise MLServiceError("'transaction_history' must be a non-empty list.", 400)
    required_fields = {"date", "gmv", "refund_count", "chargeback_count", "order_count"}
    invalid = [index for index, record in enumerate(transaction_history)
               if not isinstance(record, dict) or not required_fields.issubset(record)]
    if invalid:
        raise MLServiceError(f"Each transaction history record must contain {sorted(required_fields)} (invalid rows: {invalid}).", 400)
    from fraud.pattern_detector import detect_fraud_signals
    return {"merchant_id": merchant_id, **detect_fraud_signals(transaction_history)}


def _transaction_portfolio() -> tuple[list, list[str]]:
    _require_ml()
    from data.synthetic_transactions import TRANSACTION_FEATURES, generate_synthetic_transactions
    return generate_synthetic_transactions(), TRANSACTION_FEATURES


def _merchant_features(merchant_id: str) -> dict:
    from app.extensions import db
    from app.models import MerchantTransactionProfile
    data, feature_columns = _transaction_portfolio()
    profile = MerchantTransactionProfile.query.filter_by(merchant_id=str(merchant_id)).first()
    if profile:
        return profile.feature_dict()
    try:
        row_index = int(str(merchant_id).rsplit("-", 1)[-1]) % len(data)
    except ValueError:
        row_index = sum(ord(char) for char in str(merchant_id)) % len(data)
    features = data.iloc[row_index][feature_columns].to_dict()
    profile = MerchantTransactionProfile(
        merchant_id=str(merchant_id), **features,
        actual_monthly_gmv=100000 * (1 + float(features["gmv_trend_30d"])),
        actual_monthly_inflow=100000 * (1 + float(features["gmv_trend_90d"])),
    )
    db.session.add(profile)
    db.session.commit()
    return features


def _serialize_tier_result(result) -> dict:
    return {
        "tier": result.tier,
        "eligible": result.eligible,
        "gaps": [gap.__dict__ for gap in result.gaps],
        "overall_message": result.overall_message,
    }


def get_merchant_tier_gaps(merchant_id: str, supplied_features: dict | None = None) -> dict:
    _require_ml()
    from data.synthetic_transactions import TRANSACTION_FEATURES
    from eligibility.gap_calculator import CAPITAL_TIER_CRITERIA, rank_all_tiers

    if supplied_features is not None and any(feature not in supplied_features for feature in TRANSACTION_FEATURES):
        raise MLServiceError("Tier-gap evaluation requires all transaction feature query parameters.", 400)
    features = supplied_features or _merchant_features(merchant_id)
    for feature in TRANSACTION_FEATURES if supplied_features else []:
        features[feature] = float(features[feature])
    ranked = rank_all_tiers(features)
    eligible = [result for result in ranked if result.eligible]
    eligible_names = {result.tier for result in eligible}
    current_index = max((index for index, tier in enumerate(CAPITAL_TIER_CRITERIA) if tier["name"] in eligible_names), default=-1)
    current_tier = CAPITAL_TIER_CRITERIA[current_index]["name"] if current_index >= 0 else None
    next_tier = CAPITAL_TIER_CRITERIA[current_index + 1] if current_index + 1 < len(CAPITAL_TIER_CRITERIA) else None
    next_result = next((result for result in ranked if next_tier and result.tier == next_tier["name"]), None)
    return {
        "merchant_id": merchant_id,
        "features": features,
        "current_tier": current_tier,
        "next_tier": next_tier["name"] if next_tier else None,
        "next_tier_gap": _serialize_tier_result(next_result) if next_result else None,
        "tiers": [_serialize_tier_result(result) for result in ranked],
        "disclaimer": "Capital tier thresholds are illustrative simulated values for this demo, not real Razorpay Capital policy.",
    }


def verify_merchant_documents(merchant_id: str, declared: dict) -> dict:
    _require_ml()
    from app.extensions import db
    from app.models import MerchantDocumentVerification, MerchantTransactionProfile
    from verification.document_checker import check_document_consistency

    required = ("gst_reported_monthly_revenue", "bank_statement_avg_balance", "bank_statement_monthly_inflow")
    errors = []
    for field in required:
        if field not in declared or declared[field] in (None, ""):
            errors.append(f"'{field}' is required.")
            continue
        try:
            declared[field] = float(declared[field])
        except (TypeError, ValueError):
            errors.append(f"'{field}' must be a number.")
    if errors:
        raise MLServiceError("Invalid declared document values: " + " ".join(errors), 400)
    if any(declared[field] < 0 for field in required):
        raise MLServiceError("Declared document values cannot be negative.", 400)

    _merchant_features(merchant_id)
    profile = MerchantTransactionProfile.query.filter_by(merchant_id=str(merchant_id)).first()
    result = check_document_consistency(declared, {
        "actual_monthly_gmv": profile.actual_monthly_gmv,
        "actual_monthly_inflow": profile.actual_monthly_inflow,
    })
    verification = MerchantDocumentVerification.query.filter_by(merchant_id=str(merchant_id)).first()
    if verification is None:
        verification = MerchantDocumentVerification(merchant_id=str(merchant_id))
        db.session.add(verification)
    verification.gst_reported_monthly_revenue = declared["gst_reported_monthly_revenue"]
    verification.bank_statement_avg_balance = declared["bank_statement_avg_balance"]
    verification.bank_statement_monthly_inflow = declared["bank_statement_monthly_inflow"]
    verification.consistent = result["consistent"]
    verification.set_mismatches(result["mismatches"])
    db.session.commit()
    return verification.to_dict()


def get_merchant_document_verification(merchant_id: str) -> dict | None:
    _require_ml()
    from app.models import MerchantDocumentVerification
    verification = MerchantDocumentVerification.query.filter_by(merchant_id=str(merchant_id)).first()
    return verification.to_dict() if verification else None


def get_portfolio_exposure() -> dict:
    _require_ml()
    from collections import Counter
    from eligibility.gap_calculator import CAPITAL_TIER_CRITERIA, rank_all_tiers

    data, feature_columns = _transaction_portfolio()
    tier_counts = Counter()
    blocker_counts = Counter()
    for _, row in data.iterrows():
        features = row[feature_columns].to_dict()
        eligible_results = rank_all_tiers(features)
        eligible_names = {result.tier for result in eligible_results if result.eligible}
        current_index = max((index for index, tier in enumerate(CAPITAL_TIER_CRITERIA) if tier["name"] in eligible_names), default=-1)
        current_name = CAPITAL_TIER_CRITERIA[current_index]["name"] if current_index >= 0 else "Not yet eligible"
        tier_counts[current_name] += 1
        if current_index + 1 < len(CAPITAL_TIER_CRITERIA):
            next_result = next(result for result in eligible_results if result.tier == CAPITAL_TIER_CRITERIA[current_index + 1]["name"])
            for gap in next_result.gaps:
                blocker_counts[gap.feature] += 1

    tier_summary = []
    exposure_by_tier = {"Not yet eligible": 0}
    for tier in CAPITAL_TIER_CRITERIA:
        count = tier_counts[tier["name"]]
        exposure = count * tier["estimated_exposure"]
        exposure_by_tier[tier["name"]] = exposure
        tier_summary.append({"tier": tier["name"], "merchant_count": count, "estimated_exposure": exposure})
    tier_summary.append({"tier": "Not yet eligible", "merchant_count": tier_counts["Not yet eligible"], "estimated_exposure": 0})
    return {
        "tier_summary": tier_summary,
        "blocking_signals": [{"feature": feature, "merchant_count": count} for feature, count in blocker_counts.most_common()],
        "total_merchants": len(data),
        "total_estimated_exposure": sum(exposure_by_tier.values()),
        "disclaimer": "Merchant data, tier thresholds, and exposure amounts are synthetic illustrative demo values, not real Razorpay Capital policy.",
    }
