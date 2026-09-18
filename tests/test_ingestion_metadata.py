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
    assert first_chunk["ids"] != second_chunk["ids"]
