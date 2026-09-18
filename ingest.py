import hashlib
import os
import shutil

from pdf_processor import PDFProcessor
from llm import analyze_image
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


def ingest_pdf(
    pdf_path,
    reset_database=False
):

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

    print(
        f"Extracted {len(documents)} objects"
    )

    texts = []
    ids = []
    metadatas = []

    # =========================================
    # PROCESS
    # =========================================

    for document in documents:

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

        chunks = chunk_text(
            text
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

    # =========================================
    # STORE IN CHROMA
    # =========================================

    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

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
