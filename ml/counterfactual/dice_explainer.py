"""
DiCE counterfactual explanations (Milestone 10 / spec sections 23-25).

Given a rejected applicant, finds plausible alternative profiles that
the MODEL would predict as approved -- respecting mutable/immutable
feature constraints (never suggests changing personal_status_sex, age,
or foreign_worker) and realistic feature ranges.
"""

import os
import sys

import dice_ml
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from preprocessing.feature_config import (  # noqa: E402
    NUMERIC_FEATURES, CATEGORICAL_FEATURES, MUTABLE_FEATURES, label_for, FEATURES,
)
from config import TARGET_COLUMN  # noqa: E402

FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def _build_dice(pipeline, reference_df: pd.DataFrame):
    data_for_dice = reference_df[FEATURE_COLUMNS + [TARGET_COLUMN]].copy()

    dice_data = dice_ml.Data(
        dataframe=data_for_dice,
        continuous_features=NUMERIC_FEATURES,
        outcome_name=TARGET_COLUMN,
    )
    dice_model = dice_ml.Model(model=pipeline, backend="sklearn")
    return dice_ml.Dice(dice_data, dice_model, method="random")


def generate_counterfactual(pipeline, applicant_df: pd.DataFrame, reference_df: pd.DataFrame, total_cfs: int = 3) -> dict:
    """
    Returns:
        {
          "found": bool,
          "message": str (if not found, or a disclaimer if found),
          "current_profile": {feature: value, ...},
          "alternatives": [
             {feature: {"current": v, "suggested": v}} for each changed feature
          ] (one dict per counterfactual)
        }
    """
    try:
        dice_explainer = _build_dice(pipeline, reference_df)
        cf = dice_explainer.generate_counterfactuals(
            applicant_df[FEATURE_COLUMNS],
            total_CFs=total_cfs,
            desired_class="opposite",
            features_to_vary=MUTABLE_FEATURES,
        )
        cf_df = cf.cf_examples_list[0].final_cfs_df

        if cf_df is None or len(cf_df) == 0:
            return {
                "found": False,
                "message": "No plausible counterfactual was found within the allowed (mutable, realistic) feature ranges.",
                "current_profile": applicant_df.iloc[0][FEATURE_COLUMNS].to_dict(),
                "alternatives": [],
            }

        original = applicant_df.iloc[0][FEATURE_COLUMNS]
        alternatives = []
        for _, cf_row in cf_df.iterrows():
            changed = {}
            for col in FEATURE_COLUMNS:
                orig_val = original[col]
                new_val = cf_row[col]
                if str(orig_val) != str(new_val):
                    changed[col] = {
                        "label": label_for(col),
                        "current": orig_val,
                        "suggested": new_val,
                    }
            if changed:
                alternatives.append(changed)

        return {
            "found": len(alternatives) > 0,
            "message": (
                "Under this model, these alternative profiles would result in an approval "
                "prediction. This does NOT guarantee a real-world bank would approve the "
                "loan -- it only describes the model's behavior under changed inputs."
            ),
            "current_profile": original.to_dict(),
            "alternatives": alternatives,
        }

    except Exception as exc:  # DiCE can fail to find a feasible counterfactual
        return {
            "found": False,
            "message": f"Counterfactual generation failed: {exc}",
            "current_profile": applicant_df.iloc[0][FEATURE_COLUMNS].to_dict(),
            "alternatives": [],
        }
