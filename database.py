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
