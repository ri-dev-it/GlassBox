import datetime
import secrets

import jwt
from flask import current_app

from app.extensions import db
from app.models import User


class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def register_user(email: str, password: str, full_name: str, role: str = "applicant") -> User:
    if User.query.filter_by(email=email).first():
        raise AuthError("An account with this email already exists.", 409)

    user = User(email=email, full_name=full_name, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def authenticate_user(email: str, password: str) -> User:
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        raise AuthError("Invalid email or password.", 401)
    return user


def authenticate_google_user(email: str, full_name: str) -> User:
    """Find or create an applicant whose Google identity has been verified."""
    user = User.query.filter_by(email=email).first()
    if user:
        return user

    # OAuth-only users never use this password.  Storing a strong random hash
    # preserves the existing non-null database schema and prevents password login.
    return register_user(email, secrets.token_urlsafe(48), full_name or email.split("@", 1)[0])


def issue_token(user: User) -> str:
    payload = {
        "user_id": user.id,
        "role": user.role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")
