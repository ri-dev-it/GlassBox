import datetime
import json

from app.extensions import db


class Explanation(db.Model):
    """Stores a SHAP or LIME explanation for a prediction."""
    __tablename__ = "explanations"

    id = db.Column(db.Integer, primary_key=True)
    prediction_id = db.Column(db.Integer, db.ForeignKey("predictions.id"), nullable=False, index=True)
    method = db.Column(db.String(10), nullable=False)  # "shap" | "lime"
    contributions_json = db.Column(db.Text, nullable=False)
    plain_english = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("prediction_id", "method", name="uq_prediction_method"),
    )

    def set_contributions(self, contributions: list) -> None:
        self.contributions_json = json.dumps(contributions)

    def get_contributions(self) -> list:
        return json.loads(self.contributions_json)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "prediction_id": self.prediction_id,
            "method": self.method,
            "contributions": self.get_contributions(),
            "plain_english": self.plain_english,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
