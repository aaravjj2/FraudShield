# Model Card — FraudShield XGBoost v1.0

## Model Details

- **Model name:** FraudShield XGBoost v1.0
- **Model type:** Gradient Boosted Trees (XGBoost)
- **Training date:** 2026-04-26
- **Framework:** XGBoost 2.1+

## Intended Use

Real-time fraud detection for financial transactions. The model scores
incoming credit-card transactions and flags those likely to be fraudulent,
enabling automated blocking or manual review by fraud-operations teams.

## Dataset

Kaggle Credit Card Fraud Detection dataset.

- **Total transactions:** 284,807
- **Fraud transactions:** 492 (0.173%)
- **Features:** 30 (Time, V1-V28, Amount)
- **Source:** European cardholders, September 2013

## Training Configuration

| Hyperparameter     | Value           |
|--------------------|-----------------|
| n_estimators       | 200             |
| max_depth          | 5               |
| learning_rate      | 0.1             |
| scale_pos_weight   | 577.3           |
| eval_metric        | auc             |
| random_state       | 42              |

## Feature Preprocessing

- **Time column:** Dropped (recording order, not real time)
- **V1-V28:** Used as-is (already PCA-transformed by dataset publisher)
- **Amount:** StandardScaler fitted on training set only; scaler bundled
  into `model.pkl` for consistent inference-time transforms

## Class Imbalance Handling

The dataset has a 578:1 legitimate-to-fraud ratio. Rather than using
synthetic oversampling (SMOTE), which introduces data leakage risk on
PCA-transformed features, the model uses `scale_pos_weight = 577.3`
to upweight the minority class directly in the XGBoost loss function.

## Performance Metrics

| Metric          | Value   |
|-----------------|---------|
| F1 (fraud)      | 0.8526  |
| AUC-ROC         | 0.9772  |
| Decision threshold | 0.76 |

Threshold was optimized for F1 score on the validation split. Accuracy
is intentionally omitted as a metric because the 99.83% majority class
makes it misleading (a null model that flags nothing achieves 99.83%).

## Explainability

SHAP TreeExplainer is used for per-prediction feature attribution.

- Explainer is cached at module level (not re-created per request)
- Inference latency: < 5 ms
- SHAP attribution latency: < 1 ms

## Ethical Considerations

False positives directly impact legitimate customers whose transactions
are blocked or delayed. The 0.76 decision threshold balances fraud
catch-rate against customer friction. Deployments should include a
human-in-the-loop review queue for flagged transactions.

## Regulatory Compliance

SHAP explanations support EU AI Act Article 13 (transparency) and US
Federal Reserve SR 11-7 (model risk management) requirements for
model explainability and documentation.

## Known Limitations

1. V1-V28 are PCA components from an undisclosed feature space, which
   limits interpretability of SHAP contributions to "anonymous
   directions" rather than business-meaningful features.
2. The model is trained on a single dataset from 2013; concept drift
   may degrade performance on newer fraud patterns.
3. The dataset represents European cardholders only; performance may
   differ for other geographies or payment methods.

## Version History

| Version | Date       | Notes                              |
|---------|------------|------------------------------------|
| 1.0     | 2026-04-26 | Initial training, F1=0.8526        |
