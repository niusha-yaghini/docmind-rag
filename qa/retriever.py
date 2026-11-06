"""Hybrid retrieval: pgvector cosine search + PostgreSQL full-text search, fused with RRF."""
import re

from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document as LCDocument
from langchain_core.retrievers import BaseRetriever
from pgvector.django import CosineDistance
from pydantic import Field

from documents.models import Chunk
from documents.services.embeddings import embed_query
from documents.services.ingest import FTS_CONFIG

_WORD = re.compile(r"[A-Za-z0-9]+")


def reciprocal_rank_fusion(rank_lists: list[list[int]], k: int = 60) -> list[tuple[int, float]]:
    """Merge ranked id lists. score(id) = sum(1 / (k + rank)); best first."""
    scores: dict[int, float] = {}
    for ranking in rank_lists:
        for rank, item in enumerate(ranking, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda pair: pair[1], reverse=True)


class HybridRetriever(BaseRetriever):
    """Semantic (embedding) + keyword (FTS) retrieval over document chunks."""

    k: int = Field(default_factory=lambda: settings.RETRIEVAL_TOP_K)
    candidates: int = Field(default_factory=lambda: settings.RETRIEVAL_CANDIDATES)

    def _vector_ids(self, query_vector: list[float]) -> list[int]:
        qs = (
            Chunk.objects.annotate(distance=CosineDistance("embedding", query_vector))
            .order_by("distance")
            .values_list("id", flat=True)[: self.candidates]
        )
        return list(qs)

    def _fts_ids(self, query: str) -> list[int]:
        # OR the words together: questions are sentences, an AND match would almost never hit.
        words = list(dict.fromkeys(w.lower() for w in _WORD.findall(query) if len(w) > 1))
        if not words:
            return []
        tsquery = SearchQuery(" | ".join(words), config=FTS_CONFIG, search_type="raw")
        qs = (
            Chunk.objects.filter(search_vector=tsquery)
            .annotate(rank=SearchRank(F("search_vector"), tsquery))
            .order_by("-rank")
            .values_list("id", flat=True)[: self.candidates]
        )
        return list(qs)

    def _get_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun) -> list[LCDocument]:
        fused = reciprocal_rank_fusion(
            [self._vector_ids(embed_query(query)), self._fts_ids(query)],
            k=settings.RRF_K,
        )[: self.k]
        chunks = Chunk.objects.select_related("document").in_bulk([chunk_id for chunk_id, _ in fused])
        results: list[LCDocument] = []
        for chunk_id, score in fused:
            chunk = chunks[chunk_id]
            results.append(
                LCDocument(
                    page_content=chunk.content,
                    metadata={
                        "chunk_id": chunk.id,
                        "document_id": chunk.document_id,
                        "title": chunk.document.title,
                        "chunk_index": chunk.index,
                        "score": round(score, 5),
                    },
                )
            )
        return results
