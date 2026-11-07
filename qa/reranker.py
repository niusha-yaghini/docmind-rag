"""Second retrieval stage: re-score candidates with a local cross-encoder.

First stage (bi-encoder + full-text) is fast but compares the question and each passage separately.
A cross-encoder reads question and passage TOGETHER, which is slower but much more precise, so we only
run it on the ~20 best candidates and keep the top few.
"""
import logging
from functools import lru_cache

from django.conf import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _model():
    # Imported lazily: loading the ONNX model takes a moment and is only needed when reranking is on.
    from fastembed.rerank.cross_encoder import TextCrossEncoder

    return TextCrossEncoder(model_name=settings.RERANK_MODEL)


def rerank(query: str, passages: list[str]) -> list[float]:
    """One relevance score per passage (higher = more relevant), in the same order as `passages`."""
    return [float(score) for score in _model().rerank(query, passages)]
