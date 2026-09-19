import io
import logging
import stat
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import chromadb
import streamlit as st

from config import (
    CHROMA_PATH,
    COLLECTION_NAME,
    MAX_DATABASE_ARCHIVE_BYTES,
    MAX_DATABASE_ARCHIVE_FILES,
    MAX_DATABASE_ARCHIVE_UNCOMPRESSED_BYTES,
)

logger = logging.getLogger(__name__)


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
    if len(archive_data) > MAX_DATABASE_ARCHIVE_BYTES:
        raise ValueError("Database archive exceeds the maximum allowed size")

    archive_buffer = io.BytesIO(archive_data)
    database_path = Path(CHROMA_PATH)
    database_root = database_path.resolve()

    with zipfile.ZipFile(archive_buffer) as archive:
        if len(archive.infolist()) > MAX_DATABASE_ARCHIVE_FILES:
            raise ValueError("Database archive contains too many files")

        uncompressed_size = sum(member.file_size for member in archive.infolist())
        if uncompressed_size > MAX_DATABASE_ARCHIVE_UNCOMPRESSED_BYTES:
            raise ValueError("Database archive expands beyond the maximum allowed size")

        for member in archive.infolist():
            target_path = (database_path / member.filename).resolve()
            if not target_path.is_relative_to(database_root):
                raise ValueError("Database archive contains an unsafe file path")
            if stat.S_ISLNK(member.external_attr >> 16):
                raise ValueError("Database archive cannot contain symbolic links")

        database_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = Path(
            tempfile.mkdtemp(
                prefix=f".{database_path.name}-import-",
                dir=database_path.parent,
            )
        )
        backup_path = database_path.with_name(f".{database_path.name}-backup")

        try:
            archive.extractall(temporary_path)
            clear_chroma_cache()
            if backup_path.exists():
                shutil.rmtree(backup_path)
            if database_path.exists():
                database_path.rename(backup_path)
            temporary_path.rename(database_path)
        except Exception:
            if not database_path.exists() and backup_path.exists():
                backup_path.rename(database_path)
            raise
        finally:
            if temporary_path.exists():
                shutil.rmtree(temporary_path)
            if backup_path.exists() and database_path.exists():
                try:
                    shutil.rmtree(backup_path)
                except OSError:
                    logger.warning(
                        "Could not remove old database backup at %s",
                        backup_path,
                        exc_info=True,
                    )
