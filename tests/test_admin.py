import pytest
from django.contrib.auth import get_user_model

from documents.models import Document

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(client):
    user = get_user_model().objects.create_superuser("admin", "a@example.com", "pw12345!")
    client.force_login(user)
    return client


def test_admin_pages_load(admin_client):
    for url in [
        "/admin/documents/document/",
        "/admin/documents/document/add/",
        "/admin/documents/chunk/",
        "/admin/qa/querylog/",
    ]:
        assert admin_client.get(url).status_code == 200, url


def test_admin_upload_docx_extracts_and_indexes(admin_client, sample_files):
    with sample_files["remote_work_policy"].open("rb") as handle:
        response = admin_client.post("/admin/documents/document/add/", {"title": "", "file": handle, "full_text": ""})

    assert response.status_code == 302, response.content[:500]
    doc = Document.objects.get()
    assert doc.status == Document.Status.INDEXED
    assert doc.title == "remote_work_policy"
    assert "500 USD" in doc.full_text
    assert doc.chunks.count() >= 1


def test_admin_reindex_action(admin_client, api):
    doc_id = api.post("/api/documents/", {"title": "T", "full_text": "hello world"}, format="json").json()["id"]
    response = admin_client.post(
        "/admin/documents/document/",
        {"action": "reindex_selected", "_selected_action": [doc_id]},
        follow=True,
    )
    assert response.status_code == 200
    assert b"1 of 1 document(s) re-indexed" in response.content
