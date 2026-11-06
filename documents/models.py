from pathlib import Path

from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from pgvector.django import HnswIndex, VectorField

# Must equal settings.EMBEDDING_DIM. Kept as a literal so migrations stay stable.
EMBEDDING_DIMENSIONS = 1024


class Document(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        INDEXED = "indexed", "Indexed"
        FAILED = "failed", "Failed"

    title = models.CharField(max_length=255, blank=True, help_text="Defaults to the file name.")
    file = models.FileField(
        upload_to="documents/%Y/%m/",
        blank=True,
        validators=[FileExtensionValidator(["docx"])],
        help_text="Word document (.docx). The text is extracted and indexed automatically.",
    )
    full_text = models.TextField(blank=True, help_text="Extracted from the file, or typed/pasted directly.")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs) -> None:
        if not self.title:
            self.title = Path(self.file.name).stem if self.file else "Untitled"
        super().save(*args, **kwargs)


class Chunk(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    index = models.PositiveIntegerField()
    content = models.TextField()
    embedding = VectorField(dimensions=EMBEDDING_DIMENSIONS)
    search_vector = SearchVectorField(null=True, editable=False)

    class Meta:
        ordering = ["document_id", "index"]
        constraints = [models.UniqueConstraint(fields=["document", "index"], name="uniq_chunk_document_index")]
        indexes = [
            HnswIndex(
                name="chunk_embedding_hnsw",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
            GinIndex(fields=["search_vector"], name="chunk_search_vector_gin"),
        ]

    def __str__(self) -> str:
        return f"{self.document_id}#{self.index}"


@receiver(post_delete, sender=Document)
def delete_document_file(sender, instance: Document, **kwargs) -> None:
    """Remove the stored file when a document is deleted (API, admin single or bulk delete)."""
    if instance.file:
        instance.file.delete(save=False)
