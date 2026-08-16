"""
SHAP explanations (Milestone 7 + 19).

Uses shap.Explainer wrapping the full sklearn pipeline's predict_proba,
so it works regardless of whether the final model is Logistic Regression,
XGBoost, or RandomForest -- no per-model-type branching needed, and no
hardcoded contribution values (spec section 18/45).
"""

import os
import sys

import numpy as np
import pandas as pd
import shap

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from preprocessing.feature_config import NUMERIC_FEATURES, CATEGORICAL_FEATURES, label_for  # noqa: E402

FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def _predict_proba_positive(pipeline):
    """SHAP needs a function returning a single array of the target-class probability."""
    def f(X: np.ndarray) -> np.ndarray:
        df = pd.DataFrame(X, columns=FEATURE_COLUMNS)
        return pipeline.predict_proba(df)[:, 1]
    return f


def _background_sample(background_df: pd.DataFrame, n: int = 50) -> pd.DataFrame:
    if len(background_df) <= n:
        return background_df
    return background_df.sample(n=n, random_state=42)


def local_shap_explanation(pipeline, applicant_df: pd.DataFrame, background_df: pd.DataFrame) -> list[dict]:
    """
    Returns a per-feature contribution list for ONE applicant, sorted by
    absolute contribution descending:
        [{"feature": ..., "label": ..., "value": ..., "contribution": float, "direction": "positive"|"negative"}]
    "positive" contribution pushes toward APPROVAL; "negative" pushes toward REJECTION.
    """
    background = _background_sample(background_df[FEATURE_COLUMNS])
    explainer = shap.Explainer(_predict_proba_positive(pipeline), background)
    shap_values = explainer(applicant_df[FEATURE_COLUMNS])

    contributions = shap_values.values[0]
    results = []
    for i, col in enumerate(FEATURE_COLUMNS):
        contribution = float(contributions[i])
        results.append({
            "feature": col,
            "label": label_for(col),
            "value": applicant_df.iloc[0][col],
            "contribution": round(contribution, 4),
            "direction": "positive" if contribution >= 0 else "negative",
        })
    results.sort(key=lambda r: abs(r["contribution"]), reverse=True)
    return results


def global_shap_importance(pipeline, sample_df: pd.DataFrame, max_samples: int = 100) -> list[dict]:
    """
    Mean |SHAP value| per feature across a sample of applicants --
    answers "what generally influences the model?" for the admin dashboard.
    """
    sample = _background_sample(sample_df[FEATURE_COLUMNS], n=max_samples)
    background = _background_sample(sample_df[FEATURE_COLUMNS], n=30)
    explainer = shap.Explainer(_predict_proba_positive(pipeline), background)
    shap_values = explainer(sample)

    mean_abs = np.abs(shap_values.values).mean(axis=0)
    results = [
        {"feature": col, "label": label_for(col), "mean_abs_shap": round(float(mean_abs[i]), 4)}
        for i, col in enumerate(FEATURE_COLUMNS)
    ]
    results.sort(key=lambda r: r["mean_abs_shap"], reverse=True)
    return results
