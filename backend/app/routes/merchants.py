from flask import Blueprint, jsonify, request

from app.middleware.auth_middleware import roles_required
from app.services import ml_service
from app.services.ml_service import MLServiceError

merchants_bp = Blueprint("merchants", __name__)


@merchants_bp.post("/merchants/assess")
@roles_required("applicant", "loan_officer", "admin")
def assess_merchant():
    data = request.get_json(silent=True) or {}
    try:
        result = ml_service.assess_merchant(data)
    except MLServiceError as error:
        return jsonify({"error": error.message}), error.status_code
    return jsonify(result), 200


@merchants_bp.post("/merchants/fraud-check")
@roles_required("applicant", "loan_officer", "admin")
def fraud_check():
    data = request.get_json(silent=True) or {}
    try:
        result = ml_service.check_merchant_fraud(data.get("merchant_id"), data.get("transaction_history"))
    except MLServiceError as error:
        return jsonify({"error": error.message}), error.status_code
    return jsonify(result), 200