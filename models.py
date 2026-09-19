import os
from typing import Any

import streamlit as st
from sentence_transformers import SentenceTransformer

from dotenv import load_dotenv

load_dotenv()


EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")


@st.cache_resource(show_spinner="Loading embedding model...")
def get_embedding_model() -> Any:
    return SentenceTransformer(EMBEDDING_MODEL)
