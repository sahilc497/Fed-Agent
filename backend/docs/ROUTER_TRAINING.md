# Router Training Specification & Blueprint

## 1. Overview

The Federated Agentic Mesh uses a swappable interface (`BaseIntentRouter`) for query classification. In Phase 1, a high-performance deterministic rule-based router is provided. This document specifies the data requirements, model selection, evaluation methodology, and constraints for training and deploying a dedicated local machine-learning intent classifier in Phase 2.

---

## 2. Hardware Constraints & Feasibility Analysis

- **Host Environment:** Windows 11, Python 3.10.x.
- **System Memory:** 16 GB RAM.
- **GPU:** Integrated AMD Radeon Graphics (No CUDA / No dedicated NVIDIA VRAM).

### Training Approach Recommendation
Because the machine has 16 GB RAM and integrated Radeon graphics:
1. **Do NOT fine-tune a full 8B LLM locally** (which requires $\ge 24\text{ GB}$ VRAM for LoRA/QLoRA).
2. **Train a lightweight, high-speed encoder or SetFit / Scikit-Learn pipeline:**
   - **Option A (Recommended):** `SetFit` (Sentence Transformer Few-Shot Classifier) or a fine-tuned small encoder (e.g. `MiniLM-L6-v2`, ~80MB parameter size). It runs and trains on standard CPU/RAM within minutes and delivers $>93\%$ accuracy.
   - **Option B:** Linear SVM / Logistic Regression over sentence embeddings or TF-IDF n-grams (sub-millisecond inference, $<10\text{ MB}$ footprint).

---

## 3. Dataset Specification

### 3.1 Canonical Intent Classes (6 Classes)
1. `sales` (pipeline, deals, opportunities, client contracts)
2. `hr` (leaves, employee benefits, onboarding, performance policies)
3. `finance` (invoices, wire payments, expense guidelines, accounts payable)
4. `operations` (supply chain, logistics, facilities, inventory tracking — deferred)
5. `multi_department` (cross-department requests spanning multiple functional areas)
6. `unknown` (unrelated, ambiguous, or out-of-domain queries)

### 3.2 Dataset Size & Split
- **Target Size:** At least 300 balanced, naturally phrased prompt examples (50 per class minimum).
- **Split Distribution:**
  - Training Set: 70% (210 samples)
  - Validation Set: 15% (45 samples)
  - Test Set: 15% (45 samples)
- **Data Hygiene:** Strict deduplication; no semantic leakage across training, validation, and test splits.

---

## 4. Evaluation Criteria & Target Metrics

- **Target Test Accuracy:** $\ge 90\%$.
- **Per-Class Metrics:**
  - Precision, Recall, and F1-score computed per intent class.
  - Full confusion matrix generated.
- **Inference Latency:** $< 50\text{ ms}$ on local CPU.
- **Confidence Threshold:** Any prediction with probability $< 0.65$ automatically falls back to `unknown` intent to request clarification from the user.

---

## 5. Swapping the Model in Production

The `Orchestrator` accepts any class adhering to `BaseIntentRouter`:

```python
from app.orchestrator.router_interface import BaseIntentRouter, RouterResult, IntentLabel

class MLIntentRouter(BaseIntentRouter):
    def __init__(self, model_path: str):
        # Load local trained model artifact
        self.model = load_model(model_path)

    def classify_intent(self, query: str) -> RouterResult:
        prediction, confidence = self.model.predict(query)
        if confidence < 0.65:
            return RouterResult(IntentLabel.UNKNOWN, confidence, "Low confidence score fallback")
        return RouterResult(IntentLabel(prediction), confidence, "ML classifier prediction")
```

Instantiate the Orchestrator with `MLIntentRouter`:
```python
orchestrator = Orchestrator(db=db, router=MLIntentRouter("models/router_v1.onnx"))
```
No backend route, agent, gateway, or database modification is required.
