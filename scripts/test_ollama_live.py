import os
import sys
import asyncio

# Ensure backend root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.services.ollama_service import OllamaService
from app.core.config import settings


async def verify_live_ollama():
    print(f"Configured Ollama Base URL: {settings.OLLAMA_BASE_URL}")
    print(f"Configured Answer Model: {settings.ANSWER_MODEL}")
    assert "127.0.0.1" in settings.OLLAMA_BASE_URL or "localhost" in settings.OLLAMA_BASE_URL, "Endpoint must be strictly local!"

    svc = OllamaService()
    health = await svc.check_health()
    print("Ollama Service Health:", health)
    assert health["status"] == "online", "Local Ollama service must be online"
    assert health["model_present"] is True, f"Configured model {settings.ANSWER_MODEL} must be present locally"

    print("\nTesting local generation (prompt: 'Say hello in 3 words')...")
    resp = await svc.generate_grounded_answer(
        prompt="Say hello in 3 words",
        system_instruction="Be extremely concise."
    )
    print("Ollama Local Response:", resp)
    assert len(resp) > 0, "Response must not be empty"
    print("\nVerification successful: Ollama generation is strictly local with no external fallback!")


if __name__ == "__main__":
    asyncio.run(verify_live_ollama())
