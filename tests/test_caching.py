import database
import models
import pytest


class FakeCollection:
    pass


class FakeClient:
    def __init__(self):
        self.collection = FakeCollection()

    def get_or_create_collection(self, name):
        return self.collection


def test_chroma_client_is_cached(monkeypatch):
    calls = []

    def create_client(**kwargs):
        calls.append(kwargs)
        return FakeClient()

    database.get_chroma_client.clear()
    monkeypatch.setattr(database.chromadb, "PersistentClient", create_client)

    first = database.get_chroma_client()
    second = database.get_chroma_client()

    assert first is second
    assert len(calls) == 1


def test_chroma_cache_clear_reloads_resources(monkeypatch):
    clients = []

    def create_client(**kwargs):
        client = FakeClient()
        clients.append(client)
        return client

    database.get_collection.clear()
    database.get_chroma_client.clear()
    monkeypatch.setattr(database.chromadb, "PersistentClient", create_client)

    first = database.get_collection()
    database.clear_chroma_cache()
    second = database.get_collection()

    assert first is not second
    assert len(clients) == 2


def test_embedding_model_is_cached(monkeypatch):
    models_created = []

    class FakeEmbeddingModel:
        pass

    def create_model(model_name):
        model = FakeEmbeddingModel()
        models_created.append(model_name)
        return model

    models.get_embedding_model.clear()
    monkeypatch.setattr(models, "SentenceTransformer", create_model)

    first = models.get_embedding_model()
    second = models.get_embedding_model()

    assert first is second
    assert models_created == [models.EMBEDDING_MODEL]


def test_list_indexed_documents_deduplicates_metadata(monkeypatch):
    class DocumentCollection:
        def get(self, include):
            assert include == ["metadatas"]
            return {
                "metadatas": [
                    {"document_id": "doc-2", "source": "second.pdf"},
                    {"document_id": "doc-1", "source": "first.pdf"},
                    {"document_id": "doc-1", "source": "first.pdf"},
                ]
            }

    monkeypatch.setattr(database, "get_collection", lambda: DocumentCollection())

    assert database.list_indexed_documents() == [
        {"document_id": "doc-1", "source": "first.pdf"},
        {"document_id": "doc-2", "source": "second.pdf"},
    ]


def test_delete_document_filters_by_document_id(monkeypatch):
    class DocumentCollection:
        def __init__(self):
            self.where = None

        def delete(self, where):
            self.where = where

    collection = DocumentCollection()
    monkeypatch.setattr(database, "get_collection", lambda: collection)

    database.delete_document("doc-1")

    assert collection.where == {"document_id": "doc-1"}


def test_database_export_and_import_round_trip(monkeypatch, tmp_path):
    database_path = tmp_path / "chroma"
    database_path.mkdir()
    (database_path / "chroma.sqlite3").write_bytes(b"database contents")
    monkeypatch.setattr(database, "CHROMA_PATH", str(database_path))

    archive = database.export_database()
    (database_path / "chroma.sqlite3").write_bytes(b"changed contents")

    database.import_database(archive)

    assert (database_path / "chroma.sqlite3").read_bytes() == b"database contents"


def test_database_import_rejects_unsafe_archive_paths(monkeypatch, tmp_path):
    database_path = tmp_path / "chroma"
    monkeypatch.setattr(database, "CHROMA_PATH", str(database_path))

    import io
    import zipfile

    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, "w") as archive:
        archive.writestr("../outside.txt", "unsafe")

    with pytest.raises(ValueError, match="unsafe file path"):
        database.import_database(archive_buffer.getvalue())
