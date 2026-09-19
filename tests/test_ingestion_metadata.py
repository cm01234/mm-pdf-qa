import ingest


class FakeEmbeddingModel:
    def encode(self, texts, normalize_embeddings, show_progress_bar):
        assert normalize_embeddings is True
        assert show_progress_bar is True
        return FakeEmbeddings(len(texts))


class FakeEmbeddings:
    def __init__(self, count):
        self.count = count

    def tolist(self):
        return [[0.1, 0.2] for _ in range(self.count)]


class FakeCollection:
    def __init__(self):
        self.calls = []

    def upsert(self, **kwargs):
        self.calls.append(kwargs)


class FakeProcessor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path

    def extract(self):
        return [
            {
                "id": "text_1",
                "type": "text",
                "page": 1,
                "text": "content",
                "source": self.pdf_path.name,
            }
        ]


def test_ingestion_adds_document_metadata_and_unique_ids(monkeypatch, tmp_path):
    first_pdf = tmp_path / "first.pdf"
    second_pdf = tmp_path / "second.pdf"
    first_pdf.write_bytes(b"first document")
    second_pdf.write_bytes(b"second document")

    collection = FakeCollection()
    monkeypatch.setattr(ingest, "PDFProcessor", FakeProcessor)
    monkeypatch.setattr(ingest, "get_collection", lambda: collection)
    monkeypatch.setattr(ingest, "get_embedding_model", lambda: FakeEmbeddingModel())

    first_id = ingest.ingest_pdf(first_pdf)
    second_id = ingest.ingest_pdf(second_pdf)

    first_chunk = collection.calls[0]
    second_chunk = collection.calls[1]

    assert first_chunk["metadatas"][0]["document_id"] == first_id
    assert second_chunk["metadatas"][0]["document_id"] == second_id
    assert first_chunk["metadatas"][0]["source"] == "first.pdf"
    assert first_chunk["metadatas"][0]["page"] == 1
    assert set(first_chunk["metadatas"][0]) >= {
        "document_id",
        "source",
        "page",
        "type",
    }
    assert first_chunk["ids"] != second_chunk["ids"]


def test_ingestion_reports_progress(monkeypatch, tmp_path):
    pdf_path = tmp_path / "progress.pdf"
    pdf_path.write_bytes(b"progress document")

    collection = FakeCollection()
    progress_updates = []
    monkeypatch.setattr(ingest, "PDFProcessor", FakeProcessor)
    monkeypatch.setattr(ingest, "get_collection", lambda: collection)
    monkeypatch.setattr(ingest, "get_embedding_model", lambda: FakeEmbeddingModel())

    ingest.ingest_pdf(
        pdf_path,
        progress_callback=lambda value, message: progress_updates.append(
            (value, message)
        ),
    )

    values = [value for value, _ in progress_updates]
    assert values == sorted(values)
    assert values[0] == 0.2
    assert values[-1] == 1.0
    assert progress_updates[-1][1] == "PDF indexing complete"
