# Machine Learning Pipeline

## Dataset

UCI Statlog German Credit Data -- see `ml/data/README.md` for full
documentation (source, fields, class distribution, protected-attribute caveat).

## Pipeline

```
python data/download_dataset.py   # fetch + label the real dataset (needs internet)
python training/train.py          # train, compare, select, save
```

## Synthetic merchant model

The additive merchant-risk path is trained with `python training/train_transaction_model.py`.
Its transaction features and labels are synthetic, simulated demo data only; they are not
real Razorpay merchant data and must not be treated as confirmed underwriting policy.

`train.py` trains Logistic Regression (baseline) and XGBoost (falls back
to RandomForest if xgboost isn't installed), evaluates both on the same
held-out test set (accuracy, precision, recall, F1, ROC-AUC, confusion
matrix), and selects the winner by F1 (not accuracy alone -- the dataset
is class-imbalanced ~70/30). Nothing is hardcoded; see `ml/training/train.py`.

Artifacts saved to `ml/models/saved/`:
- `model.joblib` -- the full sklearn Pipeline (preprocessing + classifier).
- `metadata.json` -- which model won, both models' metrics, dataset sizes.

`ml/data/processed/test_with_predictions.csv` -- the held-out test set
with predictions attached, used by the fairness dashboard so it never
has to retrain or leak into training data.

## Why F1, not accuracy, decides the winner

With ~70% of applicants labeled "good credit," a model that always
predicts "approve" would score 70% accuracy while being useless. F1
balances precision and recall, which matters more for a system anyone
could actually deploy.
