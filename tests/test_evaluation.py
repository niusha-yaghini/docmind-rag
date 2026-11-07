import json
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command

from documents.models import Document
from documents.services.ingest import split_text
from qa.evaluation import first_hit_rank, score

EVAL_DIR = Path(__file__).resolve().parent.parent / "eval"

pytestmark = pytest.mark.django_db


def test_first_hit_rank_is_one_based_and_case_insensitive():
    assert first_hit_rank(["nothing", "Passwords must be 14 characters"], "must be 14 CHARACTERS") == 2
    assert first_hit_rank(["a", "b"], "zzz") is None


def test_score_hit_rate_and_mrr():
    s = score([1, 2, 6, None])  # right chunk at rank 1, 2, 6 (outside top 5), and never retrieved
    assert s.questions == 4
    assert s.hit_at_1 == 0.25 and s.hit_at_3 == 0.5 and s.hit_at_5 == 0.5
    assert s.mrr == pytest.approx((1 + 0.5 + 1 / 6 + 0) / 4)


def test_score_of_nothing_is_zero():
    assert score([]).mrr == 0.0


def test_every_expected_phrase_lives_in_exactly_one_document_and_inside_one_chunk():
    corpus = json.loads((EVAL_DIR / "corpus.json").read_text(encoding="utf-8"))
    questions = json.loads((EVAL_DIR / "questions.json").read_text(encoding="utf-8"))
    chunks = [(doc["title"], chunk) for doc in corpus for chunk in split_text(doc["text"])]
    assert len(questions) >= 20
    for item in questions:
        owners = {title for title, chunk in chunks if item["expect"].lower() in chunk.lower()}
        assert len(owners) == 1, f"{item['question']!r} -> {owners}"


def _run(*args: str) -> str:
    out = StringIO()
    call_command("evaluate", *args, stdout=out, stderr=StringIO())
    return out.getvalue()


def test_evaluate_prints_a_row_per_strategy_and_cleans_up(monkeypatch, settings):
    def fake_cross_encoder(query, passages):
        words = {w for w in query.lower().split() if len(w) > 3}
        return [float(sum(w in p.lower() for w in words)) for p in passages]

    monkeypatch.setattr("qa.retriever.rerank", fake_cross_encoder)
    output = _run()

    for name in ("vector only", "keyword only", "hybrid (RRF)", "hybrid + rerank"):
        assert name in output
    assert "hit@1" in output and "MRR" in output and "WARNING" not in output
    assert not Document.objects.filter(title__startswith="[eval] ").exists()


def test_evaluate_keep_leaves_documents_and_verbose_lists_questions(monkeypatch):
    monkeypatch.setattr("qa.retriever.rerank", lambda q, passages: [0.0] * len(passages))
    output = _run("--keep", "--verbose")

    assert Document.objects.filter(title__startswith="[eval] ").count() == 10
    assert "How many vacation days do I get per year?" in output


def test_evaluate_warns_when_the_reranker_is_unavailable(monkeypatch):
    def broken(query, passages):
        raise RuntimeError("model not downloaded")

    monkeypatch.setattr("qa.retriever.rerank", broken)
    assert "reranker model was unavailable" in _run()


def test_evaluate_uses_a_single_embedding_request(monkeypatch):
    """Free OpenRouter models are limited to a few dozen requests a day, so the command must not spend one per question."""
    from tests.conftest import fake_vector

    calls = []

    def counting_embed(texts):
        calls.append(len(texts))
        return [fake_vector(t) for t in texts]

    monkeypatch.setattr("documents.services.ingest.embed_texts", counting_embed)
    monkeypatch.setattr("qa.retriever.rerank", lambda q, passages: [0.0] * len(passages))
    _run()

    assert len(calls) == 1 and calls[0] > 40  # all chunks + all questions at once


def test_evaluate_explains_a_rate_limit(monkeypatch):
    from django.core.management.base import CommandError

    def limited(texts):
        raise RuntimeError("Error code: 429 - Rate limit exceeded")

    monkeypatch.setattr("documents.services.ingest.embed_texts", limited)
    with pytest.raises(CommandError, match="daily quota"):
        _run()
