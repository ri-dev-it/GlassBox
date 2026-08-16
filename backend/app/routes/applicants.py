from flask import Blueprint, g, jsonify

from app.middleware.auth_middleware import roles_required
from app.services import application_service

applicants_bp = Blueprint("applicants", __name__)


@applicants_bp.get("/applications")
@roles_required("applicant", "loan_officer", "admin")
def list_applications():
    if g.current_user.role == "applicant":
        applications = application_service.get_applications_for_user(g.current_user)
    else:
        applications = application_service.get_all_applications()
    return jsonify({"applications": applications}), 200


@applicants_bp.get("/applications/<int:application_id>")
@roles_required("applicant", "loan_officer", "admin")
def get_application(application_id: int):
    detail = application_service.get_application_detail(application_id, g.current_user)
    if detail is None:
        return jsonify({"error": "Application not found."}), 404
    return jsonify(detail), 200
