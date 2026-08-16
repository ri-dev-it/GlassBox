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
- **predictions** -- decision + probability + which model produced it. 1:1 with application.
- **explanations** -- SHAP and LIME rows (method column), each with contributions (JSON) + plain-English text.
- **counterfactuals** -- found/message/alternatives (JSON) per prediction.

## First admin account

Public registration only ever creates `applicant` accounts (security --
see `docs/api/README.md`). Bootstrap the first admin with:

    cd backend
    python ../database/seeds/seed_admin.py admin@example.com "Admin Name" a-strong-password

After that, admins can create more staff accounts via `POST /api/auth/create-staff`.
