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
        from data.synthetic_transactions import TRANSACTION_FEATURES, TRANSACTION_LABELS, TRANSACTION_RANGES
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
        return {
            "prediction": {
                **result,
                "risk_score": round(result["probability"] * 100),
                "risk_level": "HIGH" if result["probability"] >= 0.66 else "MEDIUM" if result["probability"] >= 0.33 else "LOW",
                "model_name": "synthetic_transaction_model",
            },
            "shap": {"contributions": contributions, "plain_english": summary},
            "disclaimer": "This assessment uses synthetic transaction data for demo purposes, not real Razorpay merchant data or policy.",
        }
    except TransactionModelNotTrainedError as e:
        raise MLServiceError(str(e), 503)
