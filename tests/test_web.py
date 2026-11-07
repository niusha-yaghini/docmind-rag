import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("name,marker", [("web:chat", "Ask your documents"), ("web:documents", "Documents"), ("web:history", "Question history")])
def test_pages_render(client, name, marker):
    response = client.get(reverse(name))

    assert response.status_code == 200
    assert marker in response.content.decode()
    assert "/static/web/app.js" in response.content.decode()


def test_root_serves_chat_and_admin_still_works(client):
    assert client.get("/").status_code == 200
    assert client.get("/admin/login/").status_code == 200
