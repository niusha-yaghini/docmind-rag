"""Test doubles: no network. Embeddings are a deterministic bag-of-words hash, the LLM is a stub."""
import math
import re
import zlib
from collections.abc import Iterator
from pathlib import Path

import pytest
from langchain_core.messages import AIMessageChunk
from langchain_core.runnables import RunnableGenerator
from rest_framework.test import APIClient

from documents.models import EMBEDDING_DIMENSIONS

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_data"
_WORD = re.compile(r"[a-z0-9]+")


def fake_vector(text: str) -> list[float]:
    vec = [0.0] * EMBEDDING_DIMENSIONS
    for word in _WORD.findall(text.lower()):
        vec[zlib.crc32(word.encode()) % EMBEDDING_DIMENSIONS] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


class FakeLLM:
    """Records the prompts it receives and answers with a fixed string."""

    def __init__(self) -> None:
        self.prompts: list[str] = []
        self.answer = "The stipend is 500 USD [1]."
        self.fail = False

    def runnable(self) -> RunnableGenerator:
        """Streams the answer word by word, like a real chat model; `.invoke()` joins the pieces."""

        def call(prompts) -> Iterator[AIMessageChunk]:
            for prompt_value in prompts:
                if self.fail:
                    raise RuntimeError("provider down")
                self.prompts.append(prompt_value.to_string())
                words = self.answer.split(" ")
                for i, word in enumerate(words):
                    yield AIMessageChunk(content=word + (" " if i < len(words) - 1 else ""))

        return RunnableGenerator(call)


@pytest.fixture(autouse=True)
def isolated_env(settings, tmp_path, monkeypatch):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.OPENROUTER_API_KEY = "test-key"
    settings.LLM_MODEL = "test/model"
    monkeypatch.setattr("documents.services.ingest.embed_texts", lambda texts: [fake_vector(t) for t in texts])
    monkeypatch.setattr("qa.retriever.embed_query", fake_vector)


@pytest.fixture
def fake_llm(monkeypatch) -> FakeLLM:
    llm = FakeLLM()
    monkeypatch.setattr("qa.chain.get_llm", llm.runnable)
    return llm


@pytest.fixture
def api() -> APIClient:
    return APIClient()


@pytest.fixture
def sample_files() -> dict[str, Path]:
    return {p.stem: p for p in SAMPLE_DIR.glob("*.docx")}


@pytest.fixture
def indexed_samples(api, sample_files):
    """All three sample docx files uploaded through the API."""
    for path in sample_files.values():
        with path.open("rb") as handle:
            response = api.post("/api/documents/", {"file": handle}, format="multipart")
        assert response.status_code == 201, response.content
        assert response.json()["status"] == "indexed"
    return sample_files
