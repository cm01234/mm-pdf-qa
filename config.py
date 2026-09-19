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
APP_PASSWORD = os.getenv("APP_PASSWORD", "")
STREAMLIT_SERVER_ADDRESS = os.getenv("STREAMLIT_SERVER_ADDRESS", "127.0.0.1")
PUBLIC_DEPLOYMENT = os.getenv("PUBLIC_DEPLOYMENT", "false").lower() in {
	"1",
	"true",
	"yes",
}
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(200 * 1024 * 1024)))
MAX_DATABASE_ARCHIVE_BYTES = int(
	os.getenv("MAX_DATABASE_ARCHIVE_BYTES", str(200 * 1024 * 1024))
)
MAX_DATABASE_ARCHIVE_FILES = int(
	os.getenv("MAX_DATABASE_ARCHIVE_FILES", "10000")
)
MAX_DATABASE_ARCHIVE_UNCOMPRESSED_BYTES = int(
	os.getenv("MAX_DATABASE_ARCHIVE_UNCOMPRESSED_BYTES", str(1024 * 1024 * 1024))
)
