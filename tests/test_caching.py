import database
import models


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
