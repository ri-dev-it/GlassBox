from flask import Blueprint, g, jsonify, request

from app.middleware.auth_middleware import roles_required
from app.schemas.application_schema import validate_application_payload
from app.services import application_service
from app.services.indian_feature_mapper import map_indian_ui_to_model
from app.services.ml_service import MLServiceError

predictions_bp = Blueprint("predictions", __name__)


@predictions_bp.post("/predict")
@roles_required("applicant", "loan_officer", "admin")
def predict():
    data = request.get_json(silent=True) or {}
    model_features = map_indian_ui_to_model(data)
    errors = validate_application_payload(model_features)
    if errors:
        return jsonify({"errors": errors}), 400

    try:
        result = application_service.submit_application(g.current_user, model_features)
    except MLServiceError as e:
        return jsonify({"error": e.message}), e.status_code

    return jsonify(result), 201
