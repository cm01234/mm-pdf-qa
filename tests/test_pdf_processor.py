from pathlib import Path

import pytest
import pdf_processor


class FakeDataFrame:
    def to_string(self, index):
        assert index is False
        return "Name Value\nA 10"


class FakeTable:
    def to_pandas(self):
        return FakeDataFrame()


class FakeTables:
    tables = [FakeTable()]


class FakePage:
    def get_text(self, mode):
        assert mode == "text"
        return "Page text"

    def find_tables(self):
        return FakeTables()

    def get_images(self, full):
        assert full is True
        return [(7,)]


class FakeDocument:
    def __iter__(self):
        return iter([FakePage()])

    def extract_image(self, xref):
        assert xref == 7
        return {"image": b"image bytes", "ext": "png"}

    def close(self):
        pass


def test_extracts_text_table_and_image(monkeypatch, tmp_path):
    monkeypatch.setattr(pdf_processor.pymupdf, "open", lambda path: FakeDocument())

    documents = pdf_processor.PDFProcessor(
        tmp_path / "report.pdf",
        output_dir=tmp_path / "images",
    ).extract()

    assert {document["type"] for document in documents} == {"text", "table", "image"}

    text_document = next(document for document in documents if document["type"] == "text")
    assert text_document["page"] == 1
    assert text_document["text"] == "Page text"

    table_document = next(document for document in documents if document["type"] == "table")
    assert "Name Value" in table_document["text"]

    image_document = next(document for document in documents if document["type"] == "image")
    image_path = Path(image_document["image_path"])
    assert image_path.exists()
    assert image_path.read_bytes() == b"image bytes"


def test_extract_reports_invalid_pdf(monkeypatch, tmp_path):
    monkeypatch.setattr(
        pdf_processor.pymupdf,
        "open",
        lambda path: (_ for _ in ()).throw(RuntimeError("invalid PDF")),
    )

    processor = pdf_processor.PDFProcessor(tmp_path / "invalid.pdf")

    with pytest.raises(ValueError, match="invalid or corrupted"):
        processor.extract()


def test_extract_reports_empty_pdf(monkeypatch, tmp_path):
    class EmptyDocument:
        def __iter__(self):
            return iter([])

        def close(self):
            pass

    monkeypatch.setattr(pdf_processor.pymupdf, "open", lambda path: EmptyDocument())

    processor = pdf_processor.PDFProcessor(tmp_path / "empty.pdf")

    with pytest.raises(ValueError, match="no extractable"):
        processor.extract()
