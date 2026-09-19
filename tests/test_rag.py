import rag


class FakeVector:
    def tolist(self):
        return [0.1, 0.2]


class FakeEmbeddingModel:
    def encode(self, questions, normalize_embeddings):
        assert len(questions) == 1
        assert normalize_embeddings is True
        return [FakeVector()]


class FakeCollection:
    def __init__(self, count=1, results=None):
        self._count = count
        self.results = results or {
            "documents": [["matching content"]],
            "metadatas": [[
                {"document_id": "doc-1", "source": "file.pdf", "page": 1, "type": "text"}
            ]],
        }
        self.query_arguments = None

    def count(self):
        return self._count

    def query(self, **kwargs):
        self.query_arguments = kwargs
        return self.results


def test_retrieve_filters_by_document_id(monkeypatch):
    collection = FakeCollection()
    monkeypatch.setattr(rag, "get_collection", lambda: collection)
    monkeypatch.setattr(rag, "get_embedding_model", lambda: FakeEmbeddingModel())

    results = rag.retrieve("question", "doc-1")

    assert results[0]["text"] == "matching content"
    assert collection.query_arguments["where"] == {"document_id": "doc-1"}
    assert collection.query_arguments["n_results"] == 15


def test_retrieve_reranks_candidates_by_query_terms(monkeypatch):
    collection = FakeCollection(results={
        "documents": [[
            "Unrelated content",
            "The report discusses revenue growth",
            "Revenue growth was strongest in the quarter",
        ]],
        "metadatas": [[
            {"document_id": "doc-1", "source": "file.pdf", "page": 1, "type": "text"},
            {"document_id": "doc-1", "source": "file.pdf", "page": 2, "type": "text"},
            {"document_id": "doc-1", "source": "file.pdf", "page": 3, "type": "text"},
        ]],
    })
    monkeypatch.setattr(rag, "get_collection", lambda: collection)
    monkeypatch.setattr(rag, "get_embedding_model", lambda: FakeEmbeddingModel())

    results = rag.retrieve("revenue growth quarter", "doc-1", k=2)

    assert [result["metadata"]["page"] for result in results] == [3, 2]


def test_retrieve_skips_embedding_for_empty_collection(monkeypatch):
    collection = FakeCollection(count=0)

    def fail_if_loaded():
        raise AssertionError("embedding model should not load")

    monkeypatch.setattr(rag, "get_collection", lambda: collection)
    monkeypatch.setattr(rag, "get_embedding_model", fail_if_loaded)

    assert rag.retrieve("question", "doc-1") == []


def test_retrieve_handles_no_matches(monkeypatch):
    collection = FakeCollection(results={"documents": [[]], "metadatas": [[]]})
    monkeypatch.setattr(rag, "get_collection", lambda: collection)
    monkeypatch.setattr(rag, "get_embedding_model", lambda: FakeEmbeddingModel())

    assert rag.retrieve("question", "doc-1") == []


def test_answer_question_marks_unsupported_answers(monkeypatch):
    monkeypatch.setattr(rag, "retrieve", lambda question, document_id: [{
        "text": "The report discusses revenue growth.",
        "metadata": {"source": "file.pdf", "page": 1, "type": "text"},
    }])
    monkeypatch.setattr(rag, "ask_llm", lambda prompt: "The capital is Paris.")

    result = rag.answer_question("What is the capital?", "doc-1")

    assert result["answer"].startswith("I could not verify that answer")


def test_answer_question_keeps_supported_answers(monkeypatch):
    monkeypatch.setattr(rag, "retrieve", lambda question, document_id: [{
        "text": "The report discusses revenue growth.",
        "metadata": {"source": "file.pdf", "page": 1, "type": "text"},
    }])
    monkeypatch.setattr(rag, "ask_llm", lambda prompt: "The report discusses revenue growth.")

    result = rag.answer_question("What does the report discuss?", "doc-1")

    assert result["answer"] == "The report discusses revenue growth."
