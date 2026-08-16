# Explainable AI Credit / Loan Approval System

Final-year engineering project. A full-stack loan approval platform that
predicts APPROVED/REJECTED using a real trained ML model, and explains
every decision with SHAP, LIME, and DiCE counterfactuals -- plus a
Fairlearn-based fairness audit across groups.

## Problem Statement

Loan approval models are often "black boxes." This system predicts the
outcome AND explains what drove it, what could plausibly change it, and
whether the model's outcomes differ across groups -- with explicit
disclaimers everywhere a number could be mistaken for a guarantee.

## Features

- ML prediction: Logistic Regression vs XGBoost, selected by actual held-out F1/ROC-AUC, not assumption
- Local + global SHAP explanations
- LIME explanations, with an explicit SHAP-vs-LIME agreement/disagreement view
- Dynamically generated plain-English explanations
- DiCE counterfactuals ("what would need to change"), respecting immutable/protected features
- Fairlearn fairness audit (selection rate, TPR/FPR by group, demographic parity, equalized odds)
- JWT auth with role-based access (applicant / loan_officer / admin); public signup can never self-assign staff roles
- Admin dashboard: model performance, global SHAP, fairness metrics, application stats

## Architecture

```
project-root/
├── frontend/    React + TypeScript + Vite + Tailwind CSS
├── backend/     Python + Flask REST API (routes -> services -> ML/DB)
├── ml/          Dataset, preprocessing, training, explainability, fairness
├── database/    MySQL schema + seed script
├── tests/       Backend (pytest), ML (pytest), frontend (Vitest)
└── docs/        Architecture, API, database, ML, explainability, fairness, testing
```

See `docs/` for the deep-dive on each area.

## Technology Stack

| Layer | Stack |
|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS, React Router, Axios, Recharts |
| Backend | Python, Flask, Flask-CORS, Flask-SQLAlchemy, Flask-Bcrypt, PyJWT |
| ML | Pandas, NumPy, scikit-learn, XGBoost, SHAP, LIME, DiCE, Fairlearn, Joblib |
| Database | MySQL |

---

## Installation

### Prerequisites

Node.js 18+, Python 3.11+, MySQL 8+, and an internet connection (to
download the dataset and install packages).

### 1. Environment

```bash
cp .env.example backend/.env
# edit backend/.env: DB credentials, a real SECRET_KEY, etc.
```

### 2. Database

```sql
CREATE DATABASE xai_loan_db CHARACTER SET utf8mb4;
```

Set `MYSQL_*` / `DATABASE_URL` in `backend/.env` to match.

### 3. Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
flask db init && flask db migrate -m "initial schema" && flask db upgrade
python run.py
```

API on **http://localhost:5000**. Verify: `curl http://localhost:5000/api/health`.

### 4. Train the model (required before predictions work)

```bash
cd ml
python data/download_dataset.py   # fetches the real UCI dataset -- needs internet
python training/train.py
```

This writes `ml/models/saved/model.joblib` + `metadata.json`, which the
backend's `/api/predict` and `/api/analytics/*` endpoints depend on --
you'll get a 503 with a clear message if you skip this step.

### 5. First admin account

```bash
cd backend
python ../database/seeds/seed_admin.py admin@example.com "Admin Name" a-strong-password
```

### 6. Frontend

```bash
cd frontend
npm install
npm run dev
```

App on **http://localhost:5173**.

### 7. Testing

```bash
cd backend && pytest ../tests/backend -v
cd ml && pytest ../tests/ml -v
cd frontend && npm run test
```

## Important Notes

- SHAP/LIME explain model behavior; they do not prove causation.
- Counterfactuals describe what would change the *model's* prediction, not a guarantee of real-world approval.
- Fairness metrics are reported with an explicit disparity threshold and a documented proxy-attribute caveat -- never as a blanket "the model is fair."
- No fabricated data, predictions, explanations, or fairness metrics anywhere -- every number comes from real computation on the real (UCI, cited) dataset.
