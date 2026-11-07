import pytest

from qa.retriever import HybridRetriever

pytestmark = pytest.mark.django_db

QUESTION = "How many characters must a password have?"


def titles(docs):
    return [d.metadata["title"] for d in docs]


def fake_cross_encoder(query: str, passages: list[str]) -> list[float]:
    """Pretends the cross-encoder loves anything about passwords, whatever the first stage thought."""
    return [10.0 if "password" in p.lower() else 0.0 for p in passages]


@pytest.fixture
def rerank_on(settings, monkeypatch):
    settings.RERANK_ENABLED = True
    monkeypatch.setattr("qa.retriever.rerank", fake_cross_encoder)


def test_rerank_promotes_the_passage_the_cross_encoder_prefers(indexed_samples, rerank_on):
    docs = HybridRetriever().invoke(QUESTION)

    assert titles(docs)[0] == "information_security_policy"
    assert docs[0].metadata["rerank_score"] == 10.0
    assert "password" in docs[0].page_content.lower()


def test_rerank_reads_a_wider_pool_than_it_returns(indexed_samples, rerank_on, monkeypatch, settings):
    seen = []
    monkeypatch.setattr("qa.retriever.rerank", lambda q, passages: seen.append(len(passages)) or fake_cross_encoder(q, passages))
    settings.RERANK_POOL = 6

    docs = HybridRetriever(k=2).invoke(QUESTION)

    assert seen == [6] and len(docs) == 2


def test_rerank_failure_falls_back_to_fused_order(indexed_samples, settings, monkeypatch):
    fused_order = [d.page_content for d in HybridRetriever().invoke(QUESTION)]  # reranking is off by default in tests

    def boom(query, passages):
        raise RuntimeError("model not available")

    settings.RERANK_ENABLED = True
    monkeypatch.setattr("qa.retriever.rerank", boom)
    docs = HybridRetriever().invoke(QUESTION)

    assert [d.page_content for d in docs] == fused_order
    assert all("rerank_score" not in d.metadata for d in docs)


def test_rerank_disabled_never_calls_the_model(indexed_samples, settings, monkeypatch):
    settings.RERANK_ENABLED = False
    monkeypatch.setattr("qa.retriever.rerank", lambda *a: pytest.fail("reranker must not run"))

    docs = HybridRetriever().invoke(QUESTION)

    assert docs and all("rerank_score" not in d.metadata for d in docs)


def test_saved_sources_carry_the_rerank_score_when_reranking_ran(api, indexed_samples, fake_llm, rerank_on):
    fake_llm.answer = "Passwords need at least 14 characters [1]."
    body = api.post("/api/ask/", {"question": QUESTION}, format="json").json()

    assert body["sources"][0]["rerank_score"] == 10.0


def test_saved_sources_have_no_rerank_score_when_reranking_is_off(api, indexed_samples, fake_llm):
    fake_llm.answer = "Passwords need at least 14 characters [1]."
    body = api.post("/api/ask/", {"question": QUESTION}, format="json").json()

    assert "rerank_score" not in body["sources"][0]
