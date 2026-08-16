"""
Shared configuration/constants for the ML pipeline.
"""

import os

ML_ROOT = os.path.dirname(os.path.abspath(__file__))

DATA_RAW_DIR = os.path.join(ML_ROOT, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(ML_ROOT, "data", "processed")
MODEL_DIR = os.path.join(ML_ROOT, "models", "saved")

RAW_DATA_FILE = os.path.join(DATA_RAW_DIR, "german_credit.csv")
TEST_SET_WITH_PREDICTIONS = os.path.join(DATA_PROCESSED_DIR, "test_with_predictions.csv")

MODEL_FILE = os.path.join(MODEL_DIR, "model.joblib")
METADATA_FILE = os.path.join(MODEL_DIR, "metadata.json")

TARGET_COLUMN = "credit_risk"          # 1 = good credit (approve), 0 = bad credit (reject)
RANDOM_STATE = 42
TEST_SIZE = 0.2

# Proxy attribute used for fairness auditing. This is DERIVED from the
# dataset's 'personal_status_sex' column (see preprocessing.py). It is a
# proxy, not a ground-truth self-reported attribute -- treat fairness
# findings on it as indicative, not definitive. See docs/fairness/.
PROTECTED_ATTRIBUTE = "sex"

os.makedirs(DATA_RAW_DIR, exist_ok=True)
os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)
