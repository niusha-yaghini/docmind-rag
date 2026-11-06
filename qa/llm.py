"""Chat model via OpenRouter (OpenAI-compatible), through LangChain."""
from django.conf import settings
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from documents.services.embeddings import ConfigurationError


def _chat_model(name: str) -> ChatOpenAI:
    return ChatOpenAI(
        model=name,
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
        temperature=0,
        timeout=settings.LLM_TIMEOUT_SECONDS,
        max_retries=1,
    )


def get_llm() -> BaseChatModel:
    """Main model, with optional fallbacks (free OpenRouter models are often rate limited)."""
    if not settings.OPENROUTER_API_KEY:
        raise ConfigurationError("OPENROUTER_API_KEY is not set.")
    if not settings.LLM_MODEL:
        raise ConfigurationError("LLM_MODEL is not set. Pick one from https://openrouter.ai/collections/free-models")
    primary = _chat_model(settings.LLM_MODEL)
    fallbacks = [_chat_model(name) for name in settings.LLM_FALLBACK_MODELS]
    return primary.with_fallbacks(fallbacks) if fallbacks else primary
