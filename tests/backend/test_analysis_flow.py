"""End-to-end API coverage for the exact payload emitted by the React form."""

from tests.backend.test_applications import register_and_login


def _ui_payload(**overrides):
    payload = {
        "checking_account_status": "10000_50000",
        "duration_months": 18,
        "credit_history": "existing credits paid back duly till now",
        "purpose": "home_loan",
        "credit_amount": 350000,
        "savings_account": "50000_100000",
        "employment_since": "4-7 years",
        "installment_rate_percent": 2,
        "personal_status_sex": "female:single",
        "other_debtors_guarantors": "none",
        "present_residence_since": 4,
        "property": "real estate",
        "age": 35,
        "other_installment_plans": "none",
        "housing": "own",
        "existing_credits_count": 1,
        "job": "skilled employee/official",
        "num_dependents": 1,
        "telephone": "registered",
        "foreign_worker": "yes",
    }
    payload.update(overrides)
    return payload


def test_three_ui_submissions_generate_complete_analysis(client):
    token = register_and_login(client, "analysis-flow@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    applications = [
        _ui_payload(),
        _ui_payload(
            checking_account_status="no_account", credit_amount=650000,
            duration_months=24, savings_account="above_100000", employment_since=">= 7 years",
            credit_history="all credits paid back duly (this bank)", installment_rate_percent=2,
        ),
        _ui_payload(
            checking_account_status="above_50000", credit_amount=150000,
            duration_months=8, savings_account="above_100000", employment_since=">= 7 years",
            credit_history="all credits paid back duly (this bank)", age=52,
        ),
    ]

    for payload in applications:
        response = client.post("/api/predict", json=payload, headers=headers)
        assert response.status_code == 201, response.get_json()
        result = response.get_json()
        assert result["prediction"]["decision"] in {"APPROVE", "REVIEW", "DECLINE"}
        assert 0 <= result["prediction"]["probability"] <= 1
        assert result["shap"]["contributions"]
        assert result["lime"]["contributions"]
        assert result["shap"]["plain_english"]
        assert result["lime"]["plain_english"]

        stored = client.get(f"/api/applications/{result['application']['id']}", headers=headers)
        assert stored.status_code == 200
        assert stored.get_json()["shap"]["contributions"]
        assert stored.get_json()["lime"]["contributions"]
