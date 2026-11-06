from django.db.models import Count
from drf_spectacular.utils import extend_schema
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from documents.models import Document
from documents.serializers import DocumentListSerializer, DocumentSerializer
from documents.services.ingest import process_document


class DocumentViewSet(viewsets.ModelViewSet):
    """Create, read, update, delete and re-index documents.

    Send a `.docx` as multipart `file`, or plain text as `full_text` (multipart or JSON).
    Indexing runs synchronously; check `status` / `error` in the response.
    """

    queryset = Document.objects.annotate(chunk_count=Count("chunks")).order_by("-created_at")
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title"]
    ordering_fields = ["created_at", "title"]

    def get_serializer_class(self):
        return DocumentListSerializer if self.action == "list" else DocumentSerializer

    def perform_create(self, serializer: DocumentSerializer) -> None:
        document = serializer.save()
        typed_text = (serializer.validated_data.get("full_text") or "").strip()
        process_document(document, extract=bool(document.file) and not typed_text)

    def perform_update(self, serializer: DocumentSerializer) -> None:
        document = serializer.save()
        data = serializer.validated_data
        if "file" in data or "full_text" in data:
            # New file without new text -> re-extract; explicit text always wins.
            process_document(document, extract="file" in data and "full_text" not in data)

    @extend_schema(request=None, responses=DocumentSerializer)
    @action(detail=True, methods=["post"])
    def reindex(self, request, pk=None) -> Response:
        """Rebuild chunks and embeddings from the stored text (e.g. after a failed indexing)."""
        document = self.get_object()
        process_document(document, extract=not document.full_text.strip() and bool(document.file))
        return Response(DocumentSerializer(document, context=self.get_serializer_context()).data)
