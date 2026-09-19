import os

from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = os.getenv("CHROMA_PATH", "data/chroma")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "pdf_documents")
DOCUMENTS_PATH = os.getenv("DOCUMENTS_PATH", "documents")
IMAGE_OUTPUT_DIR = os.getenv("IMAGE_OUTPUT_DIR", "data/images")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1200"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
RETRIEVAL_COUNT = int(os.getenv("RETRIEVAL_COUNT", "5"))
