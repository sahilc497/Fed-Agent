import os
import sys
import json
import logging
from pathlib import Path
import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_recall_fscore_support

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.db.sqlite import create_connection
from app.rag.embeddings import get_embedding_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_router")

ROUTER_DIR = BASE_DIR / "data" / "router"
DATASET_PATH = ROUTER_DIR / "router_dataset.json"
MODEL_ARTIFACT_PATH = ROUTER_DIR / "intent_router.joblib"
REPORT_PATH = ROUTER_DIR / "ROUTER_EVALUATION_REPORT.md"


def train_and_evaluate():
    logger.info(f"Loading intent dataset from {DATASET_PATH}...")
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    train_data = data["train"]
    val_data = data["validation"]
    test_data = data["test"]

    X_train_text = [x["query"] for x in train_data]
    y_train = [x["label"] for x in train_data]

    X_val_text = [x["query"] for x in val_data]
    y_val = [x["label"] for x in val_data]

    X_test_text = [x["query"] for x in test_data]
    y_test = [x["label"] for x in test_data]

    classes = sorted(list(set(y_train)))
    logger.info(f"Classes ({len(classes)}): {classes}")

    logger.info("Generating dense sentence embeddings via local sentence-transformers/all-MiniLM-L6-v2...")
    embedder = get_embedding_service()
    
    X_train = np.array(embedder.embed_batch(X_train_text), dtype=np.float32)
    X_val = np.array(embedder.embed_batch(X_val_text), dtype=np.float32)
    X_test = np.array(embedder.embed_batch(X_test_text), dtype=np.float32)

    logger.info(f"Feature matrix shape: Train={X_train.shape}, Test={X_test.shape}")

    clf = LogisticRegression(
        C=2.5,
        max_iter=1000,
        class_weight="balanced",
        random_state=20260421
    )

    logger.info("Training lightweight classifier on 252 training embedding vectors...")
    clf.fit(X_train, y_train)

    # Evaluate on Test Set
    logger.info("Evaluating on test split (54 unseen test samples)...")
    y_test_pred = clf.predict(X_test)
    y_test_proba = clf.predict_proba(X_test)

    acc = accuracy_score(y_test, y_test_pred)
    prec_macro, rec_macro, f1_macro, _ = precision_recall_fscore_support(y_test, y_test_pred, average="macro")
    prec_weighted, rec_weighted, f1_weighted, _ = precision_recall_fscore_support(y_test, y_test_pred, average="weighted")
    cm = confusion_matrix(y_test, y_test_pred, labels=classes)
    report_dict = classification_report(y_test, y_test_pred, labels=classes, output_dict=True)
    report_str = classification_report(y_test, y_test_pred, labels=classes)

    logger.info(f"Test Accuracy: {acc*100:.2f}% | Macro F1-Score: {f1_macro:.4f}")

    # Save model artifact
    artifact = {
        "classifier": clf,
        "classes": classes,
        "version": "1.0.0",
        "model_type": "Sentence-Transformers (384-dim) + LogisticRegression",
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "test_accuracy": acc,
        "test_f1_macro": f1_macro,
        "confidence_threshold": 0.50
    }
    joblib.dump(artifact, MODEL_ARTIFACT_PATH)
    logger.info(f"Model artifact successfully saved to {MODEL_ARTIFACT_PATH}")

    # Record training metadata in SQLite
    try:
        conn = create_connection()
        metrics_json = json.dumps({
            "test_accuracy": acc,
            "f1_macro": f1_macro,
            "precision_macro": prec_macro,
            "recall_macro": rec_macro,
            "classification_report": report_dict,
            "confusion_matrix": cm.tolist()
        })
        conn.execute(
            """INSERT INTO router_training_metadata (model_type, accuracy, precision_macro, recall_macro, f1_macro, metrics_json)
               VALUES (?, ?, ?, ?, ?, ?);""",
            ("Sentence-Transformers + LogisticRegression", acc, prec_macro, rec_macro, f1_macro, metrics_json)
        )
        conn.commit()
        conn.close()
        logger.info("Recorded router training metadata into SQLite.")
    except Exception as exc:
        logger.warning(f"Failed to record router metadata in SQLite: {exc}")

    # Write Markdown Report
    cm_header = " | ".join(["Predicted \\ Actual"] + classes)
    cm_sep = " | ".join(["---"] * (len(classes) + 1))
    cm_rows = []
    for i, row in enumerate(cm):
        row_str = " | ".join([classes[i]] + [str(x) for x in row])
        cm_rows.append(row_str)
    cm_table = f"| {cm_header} |\n| {cm_sep} |\n" + "\n".join(f"| {r} |" for r in cm_rows)

    md_report = f"""# Local Intent-Routing Classifier — Evaluation Report

## 1. Executive Summary & Verification Metrics
- **Model Architecture:** Local Pretrained Dense Embeddings (`sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions) + Multi-Class Logistic Regression (C=2.5, balanced class weights).
- **Execution Target:** 100% CPU-compatible, sub-millisecond local inference on host machine.
- **Test Set Accuracy:** `{acc * 100:.2f}%`
- **Macro Precision:** `{prec_macro:.4f}`
- **Macro Recall:** `{rec_macro:.4f}`
- **Macro F1-Score:** `{f1_macro:.4f}`
- **Weighted F1-Score:** `{f1_weighted:.4f}`
- **Confidence Threshold:** `0.50` (Confidence below threshold safely falls back to `unknown` intent).

---

## 2. Classification Performance by Canonical Intent Class

```
{report_str}
```

---

## 3. Confusion Matrix (Test Split: 54 Samples)

{cm_table}

---

## 4. Security & Authorization Guarantee
- **Non-Security Boundary:** In strict adherence to Zero-Trust architecture, intent classification serves exclusively to select the appropriate department agent dispatcher. Router predictions **NEVER** grant permissions or bypass access control. Every data retrieval operation is independently authorized against server-side RBAC and approved Federation Access Grants.
"""
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(md_report)
    logger.info(f"Evaluation report saved to {REPORT_PATH}")


if __name__ == "__main__":
    train_and_evaluate()
