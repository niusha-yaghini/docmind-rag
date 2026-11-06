from django.conf import settings
from rest_framework import serializers

from documents.models import Document
from documents.services.extract import DocxExtractionError, extract_docx_text


class DocumentListSerializer(serializers.ModelSerializer):
    chunk_count = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ["id", "title", "file", "status", "error", "chunk_count", "created_at", "updated_at"]
        read_only_fields = ["status", "error", "created_at", "updated_at"]

    def get_chunk_count(self, obj: Document) -> int:
        annotated = getattr(obj, "chunk_count", None)
        return annotated if annotated is not None else obj.chunks.count()


class DocumentSerializer(DocumentListSerializer):
    """Detail/create/update: also exposes the full extracted text."""

    class Meta(DocumentListSerializer.Meta):
        fields = DocumentListSerializer.Meta.fields + ["full_text"]
        extra_kwargs = {"title": {"required": False}, "file": {"required": False}}

    def get_chunk_count(self, obj: Document) -> int:
        # Always live: the queryset annotation is stale right after (re)indexing.
        return obj.chunks.count()

    def validate_file(self, value):
        if value.size > settings.MAX_UPLOAD_BYTES:
            raise serializers.ValidationError(f"File is larger than {settings.MAX_UPLOAD_BYTES // (1024 * 1024)} MB.")
        try:
            extract_docx_text(value)  # fails fast on corrupt / non-docx files
        except DocxExtractionError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        finally:
            value.seek(0)
        return value

    def validate(self, attrs):
        if self.instance is None and not attrs.get("file") and not (attrs.get("full_text") or "").strip():
            raise serializers.ValidationError("Provide a .docx `file` or a non-empty `full_text`.")
        return attrs
