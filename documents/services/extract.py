"""docx -> plain text. Paragraphs and tables are kept in document order."""
from typing import BinaryIO

from docx import Document as DocxDocument
from docx.table import Table
from docx.text.paragraph import Paragraph


class DocxExtractionError(Exception):
    """The file is not a readable .docx."""


def _table_to_text(table: Table) -> str:
    rows: list[str] = []
    for row in table.rows:
        cells: list[str] = []
        seen: set[int] = set()
        for cell in row.cells:
            # Merged cells are returned once per grid column; keep each only once.
            if id(cell._tc) in seen:
                continue
            seen.add(id(cell._tc))
            text = " ".join(cell.text.split())
            if text:
                cells.append(text)
        if cells:
            rows.append(" | ".join(cells))
    return "\n".join(rows)


def extract_docx_text(source: str | BinaryIO) -> str:
    try:
        doc = DocxDocument(source)
    except Exception as exc:  # python-docx raises several unrelated types for bad files
        raise DocxExtractionError(f"Could not read the .docx file: {exc}") from exc

    parts: list[str] = []
    for child in doc.element.body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            text = Paragraph(child, doc).text.strip()
        elif tag == "tbl":
            text = _table_to_text(Table(child, doc))
        else:
            continue
        if text:
            parts.append(text)
    return "\n\n".join(parts)
