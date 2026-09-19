import io
import shutil
import zipfile
from pathlib import Path
from typing import Any

import chromadb
import streamlit as st

from config import CHROMA_PATH, COLLECTION_NAME


@st.cache_resource
def get_chroma_client() -> Any:
    return chromadb.PersistentClient(path=CHROMA_PATH)


@st.cache_resource
def get_collection() -> Any:
    return get_chroma_client().get_or_create_collection(name=COLLECTION_NAME)


def clear_chroma_cache() -> None:
    get_collection.clear()
    get_chroma_client.clear()


def list_indexed_documents() -> list[dict[str, str]]:
    records = get_collection().get(include=["metadatas"])
    documents = {}

    for metadata in records.get("metadatas") or []:
        if not metadata or not metadata.get("document_id"):
            continue

        document_id = metadata["document_id"]
        documents[document_id] = {
            "document_id": document_id,
            "source": metadata.get("source", document_id),
        }

    return sorted(documents.values(), key=lambda document: document["source"])


def delete_document(document_id: str) -> None:
    get_collection().delete(where={"document_id": document_id})


def export_database() -> bytes:
    archive_buffer = io.BytesIO()
    database_path = Path(CHROMA_PATH)

    with zipfile.ZipFile(archive_buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        if database_path.exists():
            for file_path in database_path.rglob("*"):
                if file_path.is_file():
                    archive.write(file_path, file_path.relative_to(database_path))

    return archive_buffer.getvalue()


def import_database(archive_data: bytes) -> None:
    archive_buffer = io.BytesIO(archive_data)
    database_path = Path(CHROMA_PATH)
    database_root = database_path.resolve()

    with zipfile.ZipFile(archive_buffer) as archive:
        for member in archive.infolist():
            target_path = (database_path / member.filename).resolve()
            if not target_path.is_relative_to(database_root):
                raise ValueError("Database archive contains an unsafe file path")

        clear_chroma_cache()
        if database_path.exists():
            shutil.rmtree(database_path)
        database_path.mkdir(parents=True, exist_ok=True)
        archive.extractall(database_path)
