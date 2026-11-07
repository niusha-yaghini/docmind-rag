import time

from django.conf import settings

from qa.chain import NOT_FOUND_ANSWER, build_chain
from qa.models import QueryLog

SNIPPET_CHARS = 300


def answer_question(question: str) -> QueryLog:
    """Run the RAG chain and persist the exchange. Raises on retrieval/LLM failure (nothing is saved)."""
    started = time.perf_counter()
    result = build_chain().invoke(question)
    sources = [
        {
            "document_id": doc.metadata["document_id"],
            "title": doc.metadata["title"],
            "chunk_index": doc.metadata["chunk_index"],
            "score": doc.metadata["score"],
            "snippet": doc.page_content[:SNIPPET_CHARS],
        }
        for doc in result["docs"]
    ]
    answer = result["answer"].strip()
    if answer.startswith(NOT_FOUND_ANSWER.rstrip(".")):
        sources = []  # a refusal must not advertise unrelated passages as sources
    return QueryLog.objects.create(
        question=question,
        answer=answer,
        sources=sources,
        model=settings.LLM_MODEL,
        latency_ms=int((time.perf_counter() - started) * 1000),
    )
