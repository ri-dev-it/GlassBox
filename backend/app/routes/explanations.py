from flask import Blueprint, jsonify, request

from app.middleware.auth_middleware import roles_required
from app.schemas.application_schema import validate_application_payload
from app.services import ml_service
from app.services.ml_service import MLServiceError

explanations_bp = Blueprint("explanations", __name__)


def _predict_and_validate(data: dict):
    errors = validate_application_payload(data)
    if errors:
        return None, (jsonify({"errors": errors}), 400)
    result = ml_service.predict_application(data)
    return result, None


@explanations_bp.post("/explain/shap")
@roles_required("applicant", "loan_officer", "admin")
def explain_shap():
    """Computes a fresh local SHAP explanation for the given applicant data."""
    data = request.get_json(silent=True) or {}
    result, error_response = _predict_and_validate(data)
    if error_response:
        return error_response
    try:
        shap_result = ml_service.get_shap_explanation(data, result["prediction"], result["probability"])
    except MLServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    return jsonify({"prediction": result, **shap_result}), 200


@explanations_bp.post("/explain/lime")
@roles_required("applicant", "loan_officer", "admin")
def explain_lime():
    """Computes a fresh local LIME explanation for the given applicant data."""
    data = request.get_json(silent=True) or {}
    result, error_response = _predict_and_validate(data)
    if error_response:
        return error_response
    try:
        lime_result = ml_service.get_lime_explanation(data, result["prediction"], result["probability"])
    except MLServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    return jsonify({"prediction": result, **lime_result}), 200
