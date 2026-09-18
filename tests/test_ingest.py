from ingest import chunk_text, get_document_id


def test_chunk_text_returns_empty_for_blank_input():
    assert chunk_text("   ") == []


def test_chunk_text_preserves_short_text():
    assert chunk_text("short text") == ["short text"]


def test_chunk_text_uses_overlap():
    chunks = chunk_text("abcdefghij", chunk_size=6, overlap=2)

    assert chunks == ["abcdef", "efghij"]


def test_chunk_text_splits_long_text():
    chunks = chunk_text("a" * 13, chunk_size=5, overlap=1)

    assert chunks == ["aaaaa", "aaaaa", "aaaaa"]


def test_document_id_is_stable_and_content_based(tmp_path):
    pdf_path = tmp_path / "document.pdf"
    pdf_path.write_bytes(b"document contents")

    first_id = get_document_id(pdf_path)
    second_id = get_document_id(pdf_path)

    assert first_id == second_id
    assert len(first_id) == 16

    pdf_path.write_bytes(b"different contents")
    assert get_document_id(pdf_path) != first_id
