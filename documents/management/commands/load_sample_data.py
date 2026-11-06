from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from documents.models import Document
from documents.services.ingest import process_document


class Command(BaseCommand):
    help = "Load the .docx files from sample_data/ as documents and index them (needs the OpenRouter key)."

    def handle(self, *args, **options) -> None:
        folder = Path(settings.BASE_DIR) / "sample_data"
        files = sorted(folder.glob("*.docx"))
        if not files:
            self.stderr.write(f"No .docx files found in {folder}")
            return
        for path in files:
            title = path.stem.replace("_", " ").title()
            if Document.objects.filter(title=title).exists():
                self.stdout.write(f"skip  {title} (already loaded)")
                continue
            document = Document(title=title)
            with path.open("rb") as handle:
                document.file.save(path.name, File(handle), save=True)
            process_document(document, extract=True)
            suffix = "" if document.status == Document.Status.INDEXED else f" - {document.error}"
            self.stdout.write(f"{document.status:8} {title}{suffix}")
