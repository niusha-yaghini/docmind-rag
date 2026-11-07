from django.views.generic import TemplateView


class ChatView(TemplateView):
    template_name = "web/chat.html"
    extra_context = {"active": "chat"}


class DocumentsView(TemplateView):
    template_name = "web/documents.html"
    extra_context = {"active": "documents"}


class HistoryView(TemplateView):
    template_name = "web/history.html"
    extra_context = {"active": "history"}
