from docx import Document

from documents.services.extract import DocxExtractionError, extract_docx_text
from documents.services.ingest import split_text
from qa.retriever import reciprocal_rank_fusion

import pytest


def test_extract_keeps_order_and_tables(tmp_path):
    doc = Document()
    doc.add_paragraph("First paragraph.")
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Item"
    table.cell(0, 1).text = "Price"
    table.cell(1, 0).text = "Pen"
    table.cell(1, 1).text = "3 USD"
    doc.add_paragraph("Last paragraph.")
    path = tmp_path / "t.docx"
    doc.save(path)

    text = extract_docx_text(str(path))

    assert text.index("First paragraph.") < text.index("Item | Price") < text.index("Last paragraph.")
    assert "Pen | 3 USD" in text


def test_extract_merged_cell_is_not_duplicated(tmp_path):
    doc = Document()
    table = doc.add_table(rows=1, cols=2)
    table.cell(0, 0).merge(table.cell(0, 1)).text = "Merged"
    path = tmp_path / "m.docx"
    doc.save(path)

    assert extract_docx_text(str(path)) == "Merged"


def test_extract_rejects_non_docx(tmp_path):
    path = tmp_path / "fake.docx"
    path.write_text("not a zip")
    with pytest.raises(DocxExtractionError):
        extract_docx_text(str(path))


def test_split_text_respects_chunk_size(settings):
    settings.CHUNK_SIZE = 200
    settings.CHUNK_OVERLAP = 20
    chunks = split_text("word " * 500)
    assert len(chunks) > 5
    assert all(len(c) <= 200 for c in chunks)


def test_rrf_prefers_items_ranked_high_in_both_lists():
    fused = reciprocal_rank_fusion([[1, 2, 3], [3, 1, 4]], k=60)
    ids = [item for item, _ in fused]
    assert ids[:2] == [1, 3]  # appear in both lists
    assert set(ids) == {1, 2, 3, 4}


def test_rrf_handles_empty_lists():
    assert reciprocal_rank_fusion([[], []]) == []
    assert [i for i, _ in reciprocal_rank_fusion([[5, 6], []])] == [5, 6]
