import re
import time
from collections.abc import Iterator

from django.conf import settings
from langchain_core.documents import Document as LCDocument

from qa.chain import NOT_FOUND_ANSWER, build_answer_chain, build_chain, format_context
from qa.models import QueryLog
from qa.retriever import HybridRetriever

SNIPPET_CHARS = 300


def _save(question: str, answer: str, docs: list[LCDocument], started: float) -> QueryLog:
    """Pick the sources to show and persist the exchange."""
    answer = answer.strip()
    numbered = list(enumerate(docs, start=1))
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


def answer_question(question: str) -> QueryLog:
    """Run the RAG chain and persist the exchange. Raises on retrieval/LLM failure (nothing is saved)."""
    started = time.perf_counter()
    result = build_chain().invoke(question)
    return _save(question, result["answer"], result["docs"], started)


def stream_answer(question: str) -> Iterator[tuple[str, object]]:
    """Streaming variant. Retrieval and model setup run NOW (so their errors can still become an HTTP error);
    the returned iterator then yields ("token", text) pieces and finally ("done", QueryLog).
    A failure while the model is generating raises from the iterator and nothing is saved."""
    started = time.perf_counter()
    docs = HybridRetriever().invoke(question)
    chain = build_answer_chain() if docs else None

    def events() -> Iterator[tuple[str, object]]:
        if chain is None:  # empty index: do not spend an LLM call
            parts = [NOT_FOUND_ANSWER]
            yield "token", NOT_FOUND_ANSWER
        else:
            parts = []
            for piece in chain.stream({"context": format_context(docs), "question": question}):
                if piece:
                    parts.append(piece)
                    yield "token", piece
        yield "done", _save(question, "".join(parts), docs, started)

    return events()
