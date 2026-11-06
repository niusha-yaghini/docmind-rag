from django.contrib import admin, messages
from django.db.models import Count

from documents.models import Chunk, Document
from documents.services.ingest import process_document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "chunk_total", "created_at", "updated_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "full_text")
    readonly_fields = ("status", "error", "created_at", "updated_at")
    fields = ("title", "file", "full_text", "status", "error", "created_at", "updated_at")
    actions = ["reindex_selected"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_chunk_total=Count("chunks"))

    @admin.display(description="Chunks", ordering="_chunk_total")
    def chunk_total(self, obj: Document) -> int:
        return obj._chunk_total

    def save_model(self, request, obj, form, change) -> None:
        super().save_model(request, obj, form, change)
        changed = set(form.changed_data)
        if not change or changed & {"file", "full_text"}:
            # A new/replaced file without hand-edited text means: extract the text from the file.
            extract = bool(obj.file) and "file" in changed and "full_text" not in changed
            process_document(obj, extract=extract)
            if obj.status == Document.Status.FAILED:
                self.message_user(request, f"Indexing failed: {obj.error}", level=messages.ERROR)

    @admin.action(description="Re-index selected documents")
    def reindex_selected(self, request, queryset) -> None:
        ok = 0
        for doc in queryset:
            process_document(doc, extract=not doc.full_text.strip() and bool(doc.file))
            ok += doc.status == Document.Status.INDEXED
        self.message_user(request, f"{ok} of {queryset.count()} document(s) re-indexed.")


@admin.register(Chunk)
class ChunkAdmin(admin.ModelAdmin):
    """Read-only view of what the retriever actually sees."""

    list_display = ("id", "document", "index", "preview")
    list_filter = ("document",)
    search_fields = ("content",)
    fields = ("document", "index", "content")
    readonly_fields = ("document", "index", "content")

    @admin.display(description="Content")
    def preview(self, obj: Chunk) -> str:
        return obj.content[:100]

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False
