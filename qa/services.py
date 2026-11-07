import re
import time

from django.conf import settings

from qa.chain import NOT_FOUND_ANSWER, build_chain
from qa.models import QueryLog

SNIPPET_CHARS = 300


def answer_question(question: str) -> QueryLog:
    """Run the RAG chain and persist the exchange. Raises on retrieval/LLM failure (nothing is saved)."""
    started = time.perf_counter()
    result = build_chain().invoke(question)
    answer = result["answer"].strip()
    numbered = list(enumerate(result["docs"], start=1))
    if answer.startswith(NOT_FOUND_ANSWER.rstrip(".")):
        numbered = []  # a refusal must not advertise unrelated passages as sources
    else:
        # Show only the passages the answer actually cites; keep all if the model cited none.
        cited = {int(n) for n in re.findall(r"\[(\d+)\]", answer)}
        numbered = [(n, doc) for n, doc in numbered if n in cited] or numbered
    sources = [
        {
            "ref": n,
            "document_id": doc.metadata["document_id"],
            "title": doc.metadata["title"],
            "chunk_index": doc.metadata["chunk_index"],
            "score": doc.metadata["score"],
            "snippet": doc.page_content[:SNIPPET_CHARS],
        }
        for n, doc in numbered
    ]
    return QueryLog.objects.create(
        question=question,
        answer=answer,
        sources=sources,
        model=settings.LLM_MODEL,
        latency_ms=int((time.perf_counter() - started) * 1000),
    )
