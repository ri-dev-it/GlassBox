import datetime
import json

from app.extensions import db


class Application(db.Model):
    """One loan application submission, storing the raw feature payload."""
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(20), unique=True, nullable=True, index=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey("applicants.id"), nullable=False, index=True)
    features_json = db.Column(db.Text, nullable=False)  # raw applicant feature dict, JSON-encoded
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    prediction = db.relationship("Prediction", backref="application", uselist=False, cascade="all, delete-orphan")

    def set_features(self, features: dict) -> None:
        self.features_json = json.dumps(features)

    def get_features(self) -> dict:
        return json.loads(self.features_json)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "application_id": self.public_id or f"APP-{self.created_at.year if self.created_at else '0000'}-{self.id:04d}",
            "status": "Completed" if self.prediction else "Under Review",
            "applicant_id": self.applicant_id,
            "features": self.get_features(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
