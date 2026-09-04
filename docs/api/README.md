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
| POST | `/predict` | any | Submits an application; returns a three-band `APPROVE`/`REVIEW`/`DECLINE` decision plus explanations and persists everything. |
| GET | `/applications` | any | Applicants see their own; staff see all. |
| GET | `/applications/:id` | any | Full detail (prediction, both explanations, comparison, counterfactual). Applicants can only view their own. |

## Explanations

| Method | Path | Access | Description |
|---|---|---|---|
| POST | `/explain/shap` | any | Local SHAP explanation for the given applicant payload. |
| POST | `/explain/lime` | any | Local LIME explanation for the given applicant payload. |
| POST | `/explain/counterfactual` | any | DiCE counterfactual for the given applicant payload. |

Grounded explanations are cached after first generation:

| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/explain/<application_id>` | any | Returns a persisted explanation grounded in the application's SHAP drivers. |
| GET | `/explain/merchant/<merchant_id>` | any | Returns a persisted explanation grounded in the merchant model's SHAP drivers. |

Only feature names and signed SHAP contributions are sent to the optional LLM.
Responses that fail the driver-name grounding check, missing API keys, and LLM
errors use the deterministic system-generated template instead.

## Grounded explanations

| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/explain/<application_id>` | any | Returns a cached or newly generated plain-English explanation grounded in the application's SHAP drivers. |
| GET | `/explain/merchant/<merchant_id>` | any | Returns a cached or newly generated explanation grounded in the merchant model's SHAP drivers. |

Only feature names and signed SHAP contributions are sent to the optional
LLM; no PII or full application payload is included. If `OPENAI_API_KEY` is
unset, the call fails, or the response does not mention the top real SHAP
drivers, the deterministic system-generated template is returned instead.

## Analytics (staff/admin)

| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/analytics/model` | staff | Model metadata + comparison metrics from training. |
| GET | `/analytics/shap` | staff | Global SHAP feature importance. |
| GET | `/analytics/fairness` | staff | Fairlearn group comparison + disparity metrics. |
| GET | `/analytics/applications-summary` | staff | Total/approved/rejected counts. |
| GET | `/analytics/models` | staff | Current and historical held-out Precision, Recall, F1, and ROC-AUC for both model paths; current versions are persisted in `model_metrics`. |

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
