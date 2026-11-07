from django.urls import path

from web.views import ChatView, DocumentsView, HistoryView

app_name = "web"

urlpatterns = [
    path("", ChatView.as_view(), name="chat"),
    path("documents/", DocumentsView.as_view(), name="documents"),
    path("history/", HistoryView.as_view(), name="history"),
]
