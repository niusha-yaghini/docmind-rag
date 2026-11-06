"""Ingestion pipeline: file -> full text -> chunks -> embeddings -> pgvector + FTS index.

Runs synchronously. Failures never raise to the caller; they are recorded on the document
(`status=failed`, `error=...`) so the API and admin keep working and the document can be re-indexed.
"""
import logging

from django.conf import settings
from django.contrib.postgres.search import SearchVector
from django.db import transaction
from langchain_text_splitters import RecursiveCharacterTextSplitter

from documents.models import Chunk, Document
from documents.services.embeddings import embed_texts
from documents.services.extract import DocxExtractionError, extract_docx_text

logger = logging.getLogger(__name__)

FTS_CONFIG = "english"


def split_text(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )
    return [c for c in splitter.split_text(text) if c.strip()]


def _fail(document: Document, message: str) -> Document:
    # Text may have changed, so old chunks would be stale: drop them.
    document.chunks.all().delete()
    document.status = Document.Status.FAILED
    document.error = message
    document.save(update_fields=["full_text", "status", "error", "updated_at"])
    return document


def process_document(document: Document, *, extract: bool = False) -> Document:
    """Index `document`. With extract=True the text is first re-read from the attached file."""
    if extract and document.file:
        try:
            with document.file.open("rb") as handle:
                document.full_text = extract_docx_text(handle)
        except DocxExtractionError as exc:
            return _fail(document, str(exc))

    text = document.full_text.strip()
    if not text:
        return _fail(document, "The document has no text to index.")

    pieces = split_text(text)
    try:
        vectors = embed_texts(pieces)  # network call: keep it outside the DB transaction
    except Exception as exc:
        logger.exception("Embedding failed for document %s", document.pk)
        return _fail(document, f"Embedding failed: {exc}")

    with transaction.atomic():
        document.chunks.all().delete()
        Chunk.objects.bulk_create(
            Chunk(document=document, index=i, content=piece, embedding=vector)
            for i, (piece, vector) in enumerate(zip(pieces, vectors))
        )
        Chunk.objects.filter(document=document).update(search_vector=SearchVector("content", config=FTS_CONFIG))
        document.status = Document.Status.INDEXED
        document.error = ""
        document.save(update_fields=["full_text", "status", "error", "updated_at"])
    return document
