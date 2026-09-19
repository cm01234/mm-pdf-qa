import hashlib
import logging
import os
import re
import shutil
from typing import Any, Callable

from pdf_processor import PDFProcessor
from llm import OllamaConfigurationError, analyze_image
from database import clear_chroma_cache, get_collection
from models import get_embedding_model
from config import CHUNK_OVERLAP, CHUNK_SIZE, CHROMA_PATH

logger = logging.getLogger(__name__)


def get_document_id(pdf_path: str | os.PathLike[str]) -> str:
    with open(pdf_path, "rb") as file:
        return hashlib.sha256(file.read()).hexdigest()[:16]


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:

    text = text.strip()

    if not text:
        return []

    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", text)
        if paragraph.strip()
    ]

    if len(paragraphs) == 1:
        return _split_text(paragraphs[0], chunk_size, overlap)

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        if len(paragraph) > chunk_size:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            chunks.extend(_split_text(paragraph, chunk_size, overlap))
            continue

        candidate = (
            f"{current_chunk}\n\n{paragraph}"
            if current_chunk
            else paragraph
        )

        if len(candidate) <= chunk_size:
            current_chunk = candidate
            continue

        chunks.append(current_chunk)
        current_chunk = paragraph

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:

    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):

        end = start + chunk_size

        chunks.append(
            text[start:end]
        )

        if end >= len(text):
            break

        start = end - overlap

    return chunks


def chunk_table_text(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:

    rows = [
        row.strip()
        for row in text.splitlines()
        if row.strip()
    ]

    if not rows:
        return []

    chunks = []
    current_chunk = ""

    for row in rows:
        candidate = f"{current_chunk}\n{row}" if current_chunk else row

        if current_chunk and len(candidate) > chunk_size:
            chunks.append(current_chunk)
            current_chunk = row
        else:
            current_chunk = candidate

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def _prepare_document_text(document: dict[str, Any]) -> str:

    if document["type"] != "image":
        return document["text"]

    logger.info("Analyzing image on page %s", document["page"])

    try:
        description = analyze_image(
            document["image_path"],
            document["page"],
        )
        return (
            f"PDF: {document['source']}\n"
            f"Page: {document['page']}\n"
            f"Type: image/chart\n\n"
            f"{description}"
        )
    except OllamaConfigurationError:
        raise
    except Exception as error:
        logger.warning(
            "Vision error on page %s: %s",
            document["page"],
            error,
            exc_info=True,
        )
        return document["text"]


def _append_document_chunks(
    document: dict[str, Any],
    document_id: str,
    text: str,
    ids: list[str],
    texts: list[str],
    metadatas: list[dict[str, Any]],
) -> None:

    chunks = (
        chunk_table_text(text)
        if document["type"] == "table"
        else chunk_text(text)
    )

    for chunk_number, chunk in enumerate(chunks):
        ids.append(f"{document_id}_{document['id']}_{chunk_number}")
        texts.append(chunk)
        metadatas.append({
            "document_id": document_id,
            "source": document["source"],
            "page": document["page"],
            "type": document["type"],
        })


def _index_chunks(
    collection: Any,
    texts: list[str],
    ids: list[str],
    metadatas: list[dict[str, Any]],
    report_progress: Callable[[float, str], None],
) -> None:

    logger.info("Creating %s embeddings", len(texts))
    embeddings = get_embedding_model().encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True,
    ).tolist()
    report_progress(0.9, f"Created {len(texts)} embeddings")

    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    report_progress(1.0, "PDF indexing complete")
    logger.info("PDF successfully indexed. Chunks: %s", len(texts))


def ingest_pdf(
    pdf_path: str | os.PathLike[str],
    reset_database: bool = False,
    progress_callback: Callable[[float, str], None] | None = None,
) -> str:

    def report_progress(progress: float, message: str) -> None:
        if progress_callback:
            progress_callback(progress, message)

    logger.info("Processing %s", pdf_path)

    document_id = get_document_id(pdf_path)

    # =========================================
    # RESET
    # =========================================

    if reset_database:

        if os.path.exists(CHROMA_PATH):

            shutil.rmtree(CHROMA_PATH)

        clear_chroma_cache()

    collection = get_collection()

    # =========================================
    # EXTRACT
    # =========================================

    processor = PDFProcessor(
        pdf_path
    )

    documents = processor.extract()
    report_progress(0.2, f"Extracted {len(documents)} PDF objects")

    logger.info("Extracted %s objects", len(documents))

    texts = []
    ids = []
    metadatas = []

    # =========================================
    # PROCESS
    # =========================================

    total_documents = len(documents) or 1
    reported_pages: set[int] = set()

    for document_number, document in enumerate(documents, start=1):

        page_number = document["page"]
        page_progress = 0.2 + (
            0.6 * (document_number - 1) / total_documents
        )

        if page_number not in reported_pages:
            report_progress(
                page_progress,
                f"Processing page {page_number}",
            )
            reported_pages.add(page_number)

        if document["type"] == "image":
            report_progress(
                page_progress,
                f"Analyzing image on page {page_number}",
            )

        text = _prepare_document_text(document)

        if document["type"] == "image":
            report_progress(
                page_progress,
                f"Image analysis complete on page {page_number}",
            )

        _append_document_chunks(
            document,
            document_id,
            text,
            ids,
            texts,
            metadatas,
        )

        report_progress(
            0.2 + (0.6 * document_number / total_documents),
            f"Processed PDF object {document_number} of {len(documents)}",
        )

    _index_chunks(collection, texts, ids, metadatas, report_progress)

    return document_id


if __name__ == "__main__":

    pdf_path = (
        "documents/report.pdf"
    )

    if not os.path.exists(
        pdf_path
    ):

        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    ingest_pdf(
        pdf_path,
        reset_database=False
    )
