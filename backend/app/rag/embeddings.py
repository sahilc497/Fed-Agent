import math
import hashlib
import logging
from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np
import httpx
from app.core.config import settings
from app.core.exceptions import MeshBaseException

logger = logging.getLogger("federated_mesh.embeddings")


class EmbeddingModelUnavailableError(MeshBaseException):
    """Raised when a semantic embedding model is requested but unavailable locally."""
    pass


class BaseEmbeddingService(ABC):
    """Abstract base class for embedding providers."""
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Returns the embedding vector dimension."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Returns the identifier/name of the active model."""
        pass

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generates a normalized embedding vector for a single string."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generates normalized embedding vectors for a batch of strings."""
        pass


class LocalDeterministicEmbeddingService(BaseEmbeddingService):
    """
    TEST-ONLY / DEVELOPMENT-ONLY deterministic feature-hashing vectorizer.
    Note: This generates synthetic feature-hashed vectors for unit testing
    and isolated environments. It is NOT a neural semantic model.
    Must never be silently used in production.
    """
    def __init__(self, dimension: int = 384, model_name: str = "local-deterministic-hash-384"):
        self._dimension = dimension
        self._model_name = model_name
        logger.warning(
            "LocalDeterministicEmbeddingService is active. Notice: This provides synthetic hash vectors "
            "for unit testing and does NOT provide genuine semantic understanding."
        )

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed_text(self, text: str) -> List[float]:
        vec = np.zeros(self._dimension, dtype=np.float32)
        words = text.lower().split()
        if not words:
            return vec.tolist()

        for word in words:
            # MD5 hash modulo dimension to determine feature bucket
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dimension
            sign = 1.0 if (h // self._dimension) % 2 == 0 else -1.0
            vec[idx] += sign

        # L2 Normalization
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]


class OllamaEmbeddingService(BaseEmbeddingService):
    """
    Genuine semantic embedding provider using local Ollama HTTP API.
    Does NOT download external models. Requires Ollama to have an embedding model
    or be started with embedding support.
    """
    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        dimension: int = 384
    ):
        self._base_url = base_url or settings.OLLAMA_BASE_URL
        self._model_name = model_name or settings.EMBEDDING_MODEL
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed_text(self, text: str) -> List[float]:
        url = f"{self._base_url}/api/embeddings"
        payload = {"model": self._model_name, "prompt": text}
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    emb = resp.json().get("embedding", [])
                    arr = np.array(emb, dtype=np.float32)
                    norm = np.linalg.norm(arr)
                    if norm > 0:
                        arr = arr / norm
                    return arr.tolist()
                elif resp.status_code == 500 and "does not support embeddings" in resp.text:
                    raise EmbeddingModelUnavailableError(
                        f"Local Ollama server does not have embedding support enabled for model '{self._model_name}'. "
                        "Start Ollama with `--embeddings` or configure EMBEDDING_PROVIDER=sentence_transformers."
                    )
                else:
                    raise EmbeddingModelUnavailableError(
                        f"Ollama embedding API failed with HTTP {resp.status_code}: {resp.text}"
                    )
        except httpx.ConnectError as e:
            raise EmbeddingModelUnavailableError(
                f"Cannot connect to local Ollama on {self._base_url}. Ensure Ollama is running."
            ) from e
        except Exception as e:
            if isinstance(e, EmbeddingModelUnavailableError):
                raise
            raise EmbeddingModelUnavailableError(f"Unexpected error in Ollama embeddings: {str(e)}") from e

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]


class SentenceTransformersEmbeddingService(BaseEmbeddingService):
    """
    Genuine local neural semantic embedding service using Sentence Transformers.
    Loads locally cached weights without downloading external files when ALLOW_MODEL_DOWNLOADS=False.
    """
    def __init__(self, model_name_or_path: Optional[str] = None):
        self._model_name = model_name_or_path or settings.EMBEDDING_MODEL
        try:
            from sentence_transformers import SentenceTransformer
            # Only allow network requests if explicitly permitted by config
            self._model = SentenceTransformer(
                self._model_name,
                local_files_only=not settings.ALLOW_MODEL_DOWNLOADS
            )
            # Inspect actual model dimension
            if hasattr(self._model, "get_embedding_dimension"):
                self._dimension = self._model.get_embedding_dimension()
            else:
                self._dimension = self._model.get_sentence_embedding_dimension()
        except ImportError:
            raise EmbeddingModelUnavailableError(
                "sentence-transformers is not installed in the virtual environment. "
                "Install it with: pip install sentence-transformers"
            )
        except Exception as e:
            raise EmbeddingModelUnavailableError(
                f"Failed to load local semantic embedding model '{self._model_name}': {str(e)}. "
                "Ensure the model is cached in huggingface hub (e.g. all-MiniLM-L6-v2) or set ALLOW_MODEL_DOWNLOADS=true."
            )

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed_text(self, text: str) -> List[float]:
        vec = self._model.encode(text, normalize_embeddings=True)
        return vec.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        vecs = self._model.encode(texts, normalize_embeddings=True)
        return [v.tolist() for v in vecs]


def compute_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Computes cosine similarity between two normalized vectors."""
    a = np.array(vec1, dtype=np.float32)
    b = np.array(vec2, dtype=np.float32)
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


# Singleton instance cache for the configured service
_ACTIVE_EMBEDDING_SERVICE: Optional[BaseEmbeddingService] = None


def get_embedding_service() -> BaseEmbeddingService:
    """
    Factory to retrieve configured embedding service.
    Enforces strict security: never silently falls back to hash-based vectors
    if a semantic model is requested but fails.
    """
    global _ACTIVE_EMBEDDING_SERVICE
    if _ACTIVE_EMBEDDING_SERVICE is not None:
        return _ACTIVE_EMBEDDING_SERVICE

    provider = settings.EMBEDDING_PROVIDER.lower().strip()
    
    if provider == "sentence_transformers":
        service = SentenceTransformersEmbeddingService()
    elif provider == "ollama":
        service = OllamaEmbeddingService()
    elif provider == "local_hash":
        service = LocalDeterministicEmbeddingService(dimension=settings.EMBEDDING_DIMENSION)
    else:
        raise EmbeddingModelUnavailableError(
            f"Unsupported or unrecognized EMBEDDING_PROVIDER '{provider}'. "
            "Supported providers: 'sentence_transformers', 'ollama', 'local_hash'."
        )

    _ACTIVE_EMBEDDING_SERVICE = service
    return _ACTIVE_EMBEDDING_SERVICE


def reset_embedding_service():
    """Resets the singleton instance (useful for testing and configuration changes)."""
    global _ACTIVE_EMBEDDING_SERVICE
    _ACTIVE_EMBEDDING_SERVICE = None
