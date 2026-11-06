import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from documents.models import Chunk, Document

pytestmark = pytest.mark.django_db


def test_create_from_text(api):
    response = api.post("/api/documents/", {"title": "Notes", "full_text": "Alpha beta gamma. " * 100}, format="json")

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "indexed" and body["chunk_count"] >= 1
    assert Chunk.objects.filter(document_id=body["id"], search_vector__isnull=False).count() == body["chunk_count"]


def test_upload_docx_extracts_full_text_and_defaults_title(api, sample_files):
    with sample_files["remote_work_policy"].open("rb") as handle:
        response = api.post("/api/documents/", {"file": handle}, format="multipart")

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "indexed"
    assert body["title"] == "remote_work_policy"
    assert "500 USD" in body["full_text"]
    assert "Co-working space budget | 150 USD" in body["full_text"]  # table content is kept


def test_rejects_wrong_extension_and_corrupt_docx(api):
    txt = SimpleUploadedFile("a.txt", b"hello")
    assert api.post("/api/documents/", {"file": txt}, format="multipart").status_code == 400
    bad = SimpleUploadedFile("a.docx", b"definitely not a docx")
    assert api.post("/api/documents/", {"file": bad}, format="multipart").status_code == 400
    assert Document.objects.count() == 0


def test_requires_file_or_text(api):
    assert api.post("/api/documents/", {"title": "Empty"}, format="json").status_code == 400


def test_list_and_retrieve(api):
    doc_id = api.post("/api/documents/", {"title": "One", "full_text": "Some text."}, format="json").json()["id"]

    listing = api.get("/api/documents/").json()
    assert listing["count"] == 1
    assert "full_text" not in listing["results"][0]
    assert listing["results"][0]["chunk_count"] == 1
    assert api.get(f"/api/documents/{doc_id}/").json()["full_text"] == "Some text."
    assert api.get("/api/documents/?search=one").json()["count"] == 1
    assert api.get("/api/documents/?search=zzz").json()["count"] == 0


def test_patch_text_reindexes_but_patch_title_does_not(api, monkeypatch):
    doc_id = api.post("/api/documents/", {"title": "T", "full_text": "old content here"}, format="json").json()["id"]

    calls = []
    original = "documents.services.ingest.embed_texts"
    from documents.services import ingest

    real = ingest.embed_texts
    monkeypatch.setattr(original, lambda texts: calls.append(texts) or real(texts))

    api.patch(f"/api/documents/{doc_id}/", {"title": "Renamed"}, format="json")
    assert calls == []

    response = api.patch(f"/api/documents/{doc_id}/", {"full_text": "brand new content"}, format="json")
    assert len(calls) == 1
    assert response.json()["status"] == "indexed"
    assert list(Chunk.objects.filter(document_id=doc_id).values_list("content", flat=True)) == ["brand new content"]


def test_put_replaces_document(api):
    doc_id = api.post("/api/documents/", {"title": "T", "full_text": "first"}, format="json").json()["id"]
    response = api.put(f"/api/documents/{doc_id}/", {"title": "T2", "full_text": "second version"}, format="json")
    assert response.status_code == 200
    assert response.json()["title"] == "T2"
    assert Chunk.objects.get(document_id=doc_id).content == "second version"


def test_replacing_file_reextracts_text(api, sample_files):
    with sample_files["remote_work_policy"].open("rb") as handle:
        doc_id = api.post("/api/documents/", {"file": handle}, format="multipart").json()["id"]
    with sample_files["information_security_policy"].open("rb") as handle:
        response = api.patch(f"/api/documents/{doc_id}/", {"file": handle}, format="multipart")
    assert "14 characters" in response.json()["full_text"]
    assert "stipend" not in response.json()["full_text"]


def test_delete_removes_chunks_and_file(api, sample_files):
    with sample_files["remote_work_policy"].open("rb") as handle:
        doc_id = api.post("/api/documents/", {"file": handle}, format="multipart").json()["id"]
    stored = Document.objects.get(pk=doc_id).file.path

    assert api.delete(f"/api/documents/{doc_id}/").status_code == 204

    assert Document.objects.count() == 0 and Chunk.objects.count() == 0
    from pathlib import Path

    assert not Path(stored).exists()


def test_embedding_failure_marks_document_failed_and_reindex_recovers(api, monkeypatch):
    def boom(texts):
        raise RuntimeError("rate limited")

    monkeypatch.setattr("documents.services.ingest.embed_texts", boom)
    response = api.post("/api/documents/", {"title": "T", "full_text": "some text"}, format="json")

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "failed" and "rate limited" in body["error"]
    assert body["chunk_count"] == 0

    from tests.conftest import fake_vector

    monkeypatch.setattr("documents.services.ingest.embed_texts", lambda texts: [fake_vector(t) for t in texts])
    recovered = api.post(f"/api/documents/{body['id']}/reindex/").json()
    assert recovered["status"] == "indexed" and recovered["error"] == "" and recovered["chunk_count"] == 1
