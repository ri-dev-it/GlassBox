# API Reference

Base URL: `/api`. All endpoints except `/health`, `/auth/register`, `/auth/login`
require `Authorization: Bearer <jwt>`.

## Auth

| Method | Path | Access | Description |
|---|---|---|---|
| POST | `/auth/register` | public | Creates an `applicant` account (role is never accepted from the client). |
| POST | `/auth/login` | public | Returns a JWT + user. |
| POST | `/auth/logout` | any | Stateless -- client discards the token. |
| GET | `/auth/me` | any | Returns the current user. |
| POST | `/auth/create-staff` | admin | Creates a `loan_officer` or `admin` account. |

## Applications & Predictions

| Method | Path | Access | Description |
|---|---|---|---|
| POST | `/predict` | any | Submits an application; runs prediction + SHAP + LIME + counterfactual; persists everything. |
| GET | `/applications` | any | Applicants see their own; staff see all. |
| GET | `/applications/:id` | any | Full detail (prediction, both explanations, comparison, counterfactual). Applicants can only view their own. |

## Explanations (on-demand, without persisting)

| Method | Path | Access | Description |
|---|---|---|---|
| POST | `/explain/shap` | any | Local SHAP explanation for the given applicant payload. |
| POST | `/explain/lime` | any | Local LIME explanation for the given applicant payload. |
| POST | `/explain/counterfactual` | any | DiCE counterfactual for the given applicant payload. |

## Analytics (staff/admin)

| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/analytics/model` | staff | Model metadata + comparison metrics from training. |
| GET | `/analytics/shap` | staff | Global SHAP feature importance. |
| GET | `/analytics/fairness` | staff | Fairlearn group comparison + disparity metrics. |
| GET | `/analytics/applications-summary` | staff | Total/approved/rejected counts. |

## Merchant risk

| Method | Path | Access | Description |
|---|---|---|---|
| POST | `/merchants/<merchant_id>/verify-documents` | any | Simulated manual GST/bank-value consistency check; persists the result. |
| GET | `/merchants/<merchant_id>/verify-documents` | any | Retrieves the saved simulated verification result. |
| POST | `/merchants/assess` | any | Transaction-model assessment including persisted verification signals. |
| GET | `/merchants/<merchant_id>/tier-gaps` | any | Illustrative Capital tier qualification and next-tier gaps. |
| POST | `/merchants/fraud-check` | any | Explainable fraud-pattern checks over daily transaction history. |
| GET | `/portfolio/exposure` | staff | Synthetic portfolio tier counts, demo exposure, and common blockers. |

Document verification uses manual number entry only; it does not upload files,
perform OCR, or authenticate documents. Tier thresholds and exposure amounts
are illustrative simulated values, not real Razorpay Capital policy.

## Error format

Validation errors: `{"errors": ["message", ...]}` (400).
Other errors: `{"error": "message"}` with an appropriate status code
(401 unauthenticated, 403 forbidden, 404 not found, 503 model not trained yet).
