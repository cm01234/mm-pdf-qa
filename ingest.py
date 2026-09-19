import hashlib
import os
import re
import shutil

from pdf_processor import PDFProcessor
from llm import OllamaConfigurationError, analyze_image
from database import clear_chroma_cache, get_collection
from models import get_embedding_model


def get_document_id(pdf_path):
    with open(pdf_path, "rb") as file:
        return hashlib.sha256(file.read()).hexdigest()[:16]


def chunk_text(
    text,
    chunk_size=1200,
    overlap=200
):

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


def _split_text(text, chunk_size, overlap):

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


def chunk_table_text(text, chunk_size=1200):

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


def ingest_pdf(
    pdf_path,
    reset_database=False,
    progress_callback=None,
):

    def report_progress(progress, message):
        if progress_callback:
            progress_callback(progress, message)

    print(
        f"\nProcessing {pdf_path}"
    )

    document_id = get_document_id(pdf_path)

    # =========================================
    # RESET
    # =========================================

    if reset_database:

        if os.path.exists(
            "data/chroma"
        ):

            shutil.rmtree(
                "data/chroma"
            )

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

    print(
        f"Extracted {len(documents)} objects"
    )

    texts = []
    ids = []
    metadatas = []

    # =========================================
    # PROCESS
    # =========================================

    total_documents = len(documents) or 1

    for document_number, document in enumerate(documents, start=1):

        doc_type = document[
            "type"
        ]

        # -------------------------------------
        # IMAGE / CHART
        # -------------------------------------

        if doc_type == "image":

            print(
                f"Analyzing image "
                f"on page "
                f"{document['page']}"
            )

            try:

                description = analyze_image(
                    document["image_path"],
                    document["page"]
                )

                text = (
                    f"PDF: "
                    f"{document['source']}\n"
                    f"Page: "
                    f"{document['page']}\n"
                    f"Type: "
                    f"image/chart\n\n"
                    f"{description}"
                )

            except OllamaConfigurationError:
                raise

            except Exception as e:

                print(
                    "Vision error:",
                    e
                )

                text = document[
                    "text"
                ]

        else:

            text = document[
                "text"
            ]

        # -------------------------------------
        # CHUNK
        # -------------------------------------

        chunks = (
            chunk_table_text(text)
            if document["type"] == "table"
            else chunk_text(text)
        )

        for chunk_number, chunk in enumerate(
            chunks
        ):

            chunk_id = (
                f"{document_id}_"
                f"{document['id']}_"
                f"{chunk_number}"
            )

            ids.append(
                chunk_id
            )

            texts.append(
                chunk
            )

            metadatas.append({
                "document_id": document_id,
                "source": (
                    document["source"]
                ),
                "page": (
                    document["page"]
                ),
                "type": (
                    document["type"]
                )
            })

        report_progress(
            0.2 + (0.6 * document_number / total_documents),
            f"Processed PDF object {document_number} of {len(documents)}",
        )

    # =========================================
    # EMBEDDINGS
    # =========================================

    print(
        f"Creating "
        f"{len(texts)} embeddings..."
    )

    embeddings = get_embedding_model().encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    embeddings = embeddings.tolist()
    report_progress(0.9, f"Created {len(texts)} embeddings")

    # =========================================
    # STORE IN CHROMA
    # =========================================

    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )
    report_progress(1.0, "PDF indexing complete")

    print(
        "\n================================"
    )

    print(
        "PDF successfully indexed."
    )

    print(
        f"Chunks: {len(texts)}"
    )

    print(
        "================================\n"
    )

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
