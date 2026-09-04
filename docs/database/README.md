# Database

MySQL, accessed via SQLAlchemy (`backend/app/models/`). Reference schema
in `database/schema.sql`; in normal development, use Flask-Migrate:

    cd backend
    flask db init      # once
    flask db migrate -m "initial schema"
    flask db upgrade

## Tables

- **users** -- login credentials, role (`applicant` / `loan_officer` / `admin`).
- **applicants** -- one per user; kept separate from `users` so a future
  "apply on someone else's behalf" flow doesn't require restructuring.
- **applications** -- raw submitted feature payload (JSON-encoded), one row per submission.
- **predictions** -- three-band decision (`APPROVE`, `REVIEW`, or `DECLINE`) + probability + model. Legacy `APPROVED`/`REJECTED` values remain readable in historical rows.
- **explanations** -- SHAP and LIME rows (method column), each with contributions (JSON) + plain-English text.
- **counterfactuals** -- found/message/alternatives (JSON) per prediction.
- **documents** and **document_verifications** -- uploaded document metadata and existing optional OCR-style review records.
- **bank_eligibility_results** -- legacy per-application educational bank-profile results.
- **merchant_transaction_profiles** -- persisted transaction behavior features plus actual monthly GMV/inflow used by merchant checks.
- **merchant_transaction_history** -- daily GMV, order, refund, and chargeback records for fraud review.
- **merchant_fraud_checks** -- persisted fraud score, rule flags, and flagged days.
- **merchant_tier_assessments** -- persisted Capital tier-gap results.
- **portfolio_exposure_snapshots** -- portfolio tier counts, simulated exposure, and blocking-signal summaries.
- **merchant_document_verifications** -- manual declared GST/bank values and consistency results, separate from uploaded-document verification.
- **model_metrics** -- held-out precision, recall, F1, and ROC-AUC snapshots for both income-based and transaction-based model versions.
- **governance_checks** -- historical fairness gate pass/fail decisions and failed checks per model version.
- **grounded_explanations** -- cached plain-English SHAP explanations keyed to an application or merchant, including source and driver names.
- **grounded_explanations** -- cached plain-English explanations keyed to an application or merchant, with source (`llm`/`template`) and SHAP driver names.

The merchant risk tables are additive to the original loan schema. Apply the
latest migration with `flask db upgrade`; `database/schema.sql` is also kept
as a complete fresh-MySQL reference. Capital thresholds and exposure amounts
are illustrative demo values, not real Razorpay Capital policy.

The existing `predictions.decision` column is already a string (`VARCHAR(20)`),
so no boolean-to-enum migration is required; new three-band values fit without
rewriting historical records.

## First admin account

Public registration only ever creates `applicant` accounts (security --
see `docs/api/README.md`). Bootstrap the first admin with:

    cd backend
    python ../database/seeds/seed_admin.py admin@example.com "Admin Name" a-strong-password

After that, admins can create more staff accounts via `POST /api/auth/create-staff`.
