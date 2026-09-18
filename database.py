import chromadb
import streamlit as st


CHROMA_PATH = "data/chroma"
COLLECTION_NAME = "pdf_documents"


@st.cache_resource
def get_chroma_client():
    return chromadb.PersistentClient(path=CHROMA_PATH)


@st.cache_resource
def get_collection():
    return get_chroma_client().get_or_create_collection(name=COLLECTION_NAME)


def clear_chroma_cache():
    get_collection.clear()
    get_chroma_client.clear()
