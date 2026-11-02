import os
import logging
from typing import Optional
from pathlib import Path
import joblib
import numpy as np
from app.core.config import settings
from app.orchestrator.router_interface import BaseIntentRouter, RouterResult, IntentLabel, RuleBasedIntentRouter
from app.rag.embeddings import get_embedding_service

logger = logging.getLogger("federated_mesh.router.ml")


class MLIntentRouter(BaseIntentRouter):
    """
    Locally trained ML Intent Router combining local sentence embeddings with Logistic Regression.
    Adheres strictly to BaseIntentRouter interface.
    """
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or settings.ROUTER_MODEL_PATH
        self.artifact = None
        self.classifier = None
        self.classes = None
        self.confidence_threshold = 0.45
        self.fallback_router = RuleBasedIntentRouter()
        self._load_model()

    def _load_model(self):
        p = Path(self.model_path)
        if not p.is_absolute():
            # Check relative to backend or root
            if Path("backend").is_dir():
                p = Path("backend") / p if not str(p).startswith("backend") else p
            elif Path("..").resolve().name == "Fedral-Agent" or Path("app").is_dir():
                if str(p).startswith("backend/"):
                    p = Path(str(p).replace("backend/", "", 1))
                elif str(p).startswith("backend\\"):
                    p = Path(str(p).replace("backend\\", "", 1))

        if p.exists():
            try:
                self.artifact = joblib.load(str(p))
                self.classifier = self.artifact.get("classifier") or self.artifact.get("pipeline")
                self.classes = self.artifact.get("classes")
                self.confidence_threshold = self.artifact.get("confidence_threshold", 0.45)
                logger.info(f"Loaded trained ML intent router model from {p} (accuracy: {self.artifact.get('test_accuracy', 0.0):.2f})")
            except Exception as e:
                logger.warning(f"Could not load ML router artifact: {e}. Using rule fallback.")
                self.classifier = None
        else:
            logger.warning(f"ML router artifact not found at {p}. Operating in rule fallback mode.")
            self.classifier = None

    def classify_intent(self, query: str) -> RouterResult:
        """Classifies a user query into one of the 6 canonical intent classes."""
        q_lower = query.lower().strip()
        if not q_lower:
            return RouterResult(IntentLabel.UNKNOWN, 0.0, "Empty query received.")

        # If model is not loaded, use fallback rule router
        if self.classifier is None:
            return self.fallback_router.classify_intent(query)

        try:
            embedder = get_embedding_service()
            vec = np.array([embedder.embed_text(query)], dtype=np.float32)
            
            probas = self.classifier.predict_proba(vec)[0]
            max_idx = int(np.argmax(probas))
            confidence = float(probas[max_idx])
            pred_class = self.classes[max_idx]

            # If confidence is below threshold, check fallback router for high-confidence direct match
            if confidence < self.confidence_threshold:
                fb_result = self.fallback_router.classify_intent(query)
                if fb_result.intent != IntentLabel.UNKNOWN and fb_result.confidence >= 0.80:
                    return fb_result
                return RouterResult(
                    intent=IntentLabel.UNKNOWN,
                    confidence=round(confidence, 3),
                    explanation=f"Low model confidence ({confidence:.2f} < {self.confidence_threshold}) across classes."
                )

            # Map predicted class string to IntentLabel enum
            try:
                intent_enum = IntentLabel(pred_class)
            except ValueError:
                intent_enum = IntentLabel.UNKNOWN

            # High-confidence domain keyword verification:
            # If deterministic rule router matches explicit department keywords (>= 0.85),
            # prioritize the unambiguous keyword intent over statistical classifier confusion
            fb_result = self.fallback_router.classify_intent(query)
            if fb_result.intent != IntentLabel.UNKNOWN and fb_result.confidence >= 0.85:
                if intent_enum != fb_result.intent:
                    return fb_result

            return RouterResult(
                intent=intent_enum,
                confidence=round(confidence, 3),
                explanation=f"ML intent classifier prediction: '{pred_class}' (confidence: {confidence:.2f})"
            )
        except Exception as exc:
            logger.warning(f"ML intent classification failed: {exc}. Using fallback router.")
            return self.fallback_router.classify_intent(query)
