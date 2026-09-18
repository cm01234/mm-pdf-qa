import pytest

import llm


def test_connection_failure_has_actionable_message(monkeypatch):
    def raise_connection_error(**kwargs):
        raise RuntimeError("All connection attempts failed")

    monkeypatch.setattr(llm.ollama, "chat", raise_connection_error)

    with pytest.raises(llm.OllamaConfigurationError, match="ollama serve"):
        llm.chat_with_ollama(model="test", messages=[])


def test_missing_model_has_pull_instruction(monkeypatch):
    class FakeResponseError(Exception):
        def __init__(self, message, status_code):
            super().__init__(message)
            self.status_code = status_code

    def raise_missing_model(**kwargs):
        raise FakeResponseError("model not found", status_code=404)

    monkeypatch.setattr(llm.ollama, "ResponseError", FakeResponseError)
    monkeypatch.setattr(llm.ollama, "chat", raise_missing_model)

    with pytest.raises(llm.OllamaConfigurationError, match="ollama pull"):
        llm.chat_with_ollama(model="test", messages=[])
