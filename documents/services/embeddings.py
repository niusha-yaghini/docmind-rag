"""Embeddings via OpenRouter (OpenAI-compatible endpoint), through LangChain."""
from django.conf import settings
from langchain_openai import OpenAIEmbeddings


class ConfigurationError(Exception):
    """A required setting (e.g. the OpenRouter API key) is missing."""


def get_embeddings() -> OpenAIEmbeddings:
    if not settings.OPENROUTER_API_KEY:
        raise ConfigurationError("OPENROUTER_API_KEY is not set.")
    return OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
        chunk_size=settings.EMBEDDING_BATCH_SIZE,  # texts per request
        # Non-OpenAI models: send raw strings instead of tiktoken token ids.
        check_embedding_ctx_length=False,
        timeout=settings.LLM_TIMEOUT_SECONDS,
        max_retries=3,
    )


def _check_dim(vector: list[float]) -> list[float]:
    if len(vector) != settings.EMBEDDING_DIM:
        raise ValueError(
            f"Embedding model returned {len(vector)} dimensions, expected {settings.EMBEDDING_DIM}. "
            "Fix EMBEDDING_MODEL / EMBEDDING_DIM and the VectorField size."
        )
    return vector


def embed_texts(texts: list[str]) -> list[list[float]]:
    return [_check_dim(v) for v in get_embeddings().embed_documents(texts)]


def embed_query(text: str) -> list[float]:
    return _check_dim(get_embeddings().embed_query(text))
