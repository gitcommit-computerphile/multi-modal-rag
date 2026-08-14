from config import get_settings
from models.embedding_client import OpenAIEmbeddingClient
from models.vision_client import AnthropicVisionClient, OpenAIVisionClient, VisionModelClient


def get_vision_client() -> VisionModelClient:
    settings = get_settings()
    if settings.vlm_provider == "anthropic":
        return AnthropicVisionClient(
            model=settings.vlm_model, api_key=settings.anthropic_api_key
        )
    elif settings.vlm_provider == "openai":
        return OpenAIVisionClient(
            model=settings.vlm_model, api_key=settings.openai_api_key
        )
    raise ValueError(f"Unknown VLM provider: {settings.vlm_provider}")


def get_embedding_client():
    settings = get_settings()
    if settings.embedding_provider == "openai":
        return OpenAIEmbeddingClient(
            model=settings.embedding_model, api_key=settings.openai_api_key
        )
    raise ValueError(f"Unknown embedding provider: {settings.embedding_provider}")
