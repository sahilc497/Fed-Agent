# Local Intent-Routing Classifier — Evaluation Report

## 1. Executive Summary & Verification Metrics
- **Model Architecture:** Local Pretrained Dense Embeddings (`sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions) + Multi-Class Logistic Regression (C=2.5, balanced class weights).
- **Execution Target:** 100% CPU-compatible, sub-millisecond local inference on host machine.
- **Test Set Accuracy:** `90.74%`
- **Macro Precision:** `0.9148`
- **Macro Recall:** `0.9074`
- **Macro F1-Score:** `0.9092`
- **Weighted F1-Score:** `0.9092`
- **Confidence Threshold:** `0.50` (Confidence below threshold safely falls back to `unknown` intent).

---

## 2. Classification Performance by Canonical Intent Class

```
                  precision    recall  f1-score   support

         finance       1.00      0.89      0.94         9
              hr       1.00      0.89      0.94         9
multi_department       0.89      0.89      0.89         9
      operations       0.90      1.00      0.95         9
           sales       0.70      0.78      0.74         9
         unknown       1.00      1.00      1.00         9

        accuracy                           0.91        54
       macro avg       0.91      0.91      0.91        54
    weighted avg       0.91      0.91      0.91        54

```

---

## 3. Confusion Matrix (Test Split: 54 Samples)

| Predicted \ Actual | finance | hr | multi_department | operations | sales | unknown |
| --- | --- | --- | --- | --- | --- | --- |
| finance | 8 | 0 | 0 | 0 | 1 | 0 |
| hr | 0 | 8 | 0 | 0 | 1 | 0 |
| multi_department | 0 | 0 | 8 | 0 | 1 | 0 |
| operations | 0 | 0 | 0 | 9 | 0 | 0 |
| sales | 0 | 0 | 1 | 1 | 7 | 0 |
| unknown | 0 | 0 | 0 | 0 | 0 | 9 |

---

## 4. Security & Authorization Guarantee
- **Non-Security Boundary:** In strict adherence to Zero-Trust architecture, intent classification serves exclusively to select the appropriate department agent dispatcher. Router predictions **NEVER** grant permissions or bypass access control. Every data retrieval operation is independently authorized against server-side RBAC and approved Federation Access Grants.
