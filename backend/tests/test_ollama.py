import pytest
from app.services.ollama_service import OllamaService
from app.core.exceptions import LLMServiceUnavailableError
from app.core.config import settings


def test_ollama_configured_model():
    service = OllamaService()
    # Confirms adapter uses verified local installed model
    assert service.model_name == settings.ANSWER_MODEL
    assert service.model_name == "qwen3:8b"


@pytest.mark.asyncio
async def test_ollama_unavailable_raises_controlled_error():
    # Point to an invalid unreachable port to test offline error handling
    service = OllamaService(base_url="http://127.0.0.1:59999", timeout=1)
    with pytest.raises(LLMServiceUnavailableError) as exc_info:
        await service.generate_grounded_answer(prompt="Test prompt")

    assert "Unable to connect" in str(exc_info.value) or "timed out" in str(exc_info.value)
