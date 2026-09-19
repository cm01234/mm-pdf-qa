import hmac
import hashlib
import ipaddress
import os

import streamlit as st

from ingest import ingest_pdf
from rag import answer_question
from config import (
    APP_PASSWORD,
    DOCUMENTS_PATH,
    MAX_UPLOAD_BYTES,
    PUBLIC_DEPLOYMENT,
    STREAMLIT_SERVER_ADDRESS,
)
from database import (
    delete_document,
    export_database,
    import_database,
    list_indexed_documents,
)
from file_utils import sanitize_filename


def save_uploaded_pdf(uploaded_file):
    os.makedirs(DOCUMENTS_PATH, exist_ok=True)
    file_bytes = uploaded_file.getvalue()
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise ValueError("Uploaded PDF exceeds the maximum allowed size")

    file_hash = hashlib.sha256(file_bytes).hexdigest()[:12]
    safe_name = sanitize_filename(uploaded_file.name)
    stem, suffix = os.path.splitext(safe_name)
    pdf_path = os.path.join(
        DOCUMENTS_PATH,
        f"{stem}_{file_hash}{suffix}",
    )

    with open(pdf_path, "wb") as file:
        file.write(file_bytes)

    return pdf_path


st.set_page_config(page_title="Local PDF CLANKER", layout="wide")

def _is_loopback_address(address: str) -> bool:
    if address in {"localhost", "127.0.0.1", "::1"}:
        return True
    try:
        return ipaddress.ip_address(address).is_loopback
    except ValueError:
        return False


requires_password = PUBLIC_DEPLOYMENT or not _is_loopback_address(
    STREAMLIT_SERVER_ADDRESS
)

if APP_PASSWORD:
    entered_password = st.text_input("App password", type="password")
    if not hmac.compare_digest(entered_password, APP_PASSWORD):
        st.info("Enter the configured app password to continue.")
        st.stop()
elif requires_password:
    st.error("APP_PASSWORD must be configured for public deployments.")
    st.stop()

st.title("Local PDF CLANKER Assistant")
st.caption("PDF + RAG + Qwen3-VL + ChromaDB")

with st.expander("How to use", expanded=True):
    st.markdown(
        "1. Upload a PDF from the sidebar.\n"
        "2. Click **Process PDF** to index its text, tables, and images.\n"
        "3. Ask questions about the document in the chat box below."
    )

# SESSION
if "messages" not in st.session_state:
    st.session_state.messages = []
if "document_ids" not in st.session_state:
    st.session_state.document_ids = []

# SIDEBAR
with st.sidebar:
    st.header("PDF")
    uploaded_files = st.file_uploader(
        "Upload PDF files",
        type=["pdf"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        st.success(f"{len(uploaded_files)} PDF file(s) selected")
        reset = st.checkbox("Clear existing database")

        if st.button("Process PDF", type="primary"):
            with st.spinner("Processing PDF..."):
                try:
                    st.session_state.document_ids = []

                    progress = st.progress(0, text="Starting PDF processing...")

                    def update_progress(value, message):
                        progress.progress(value, text=message)

                    for file_number, uploaded_file in enumerate(uploaded_files):
                        pdf_path = save_uploaded_pdf(uploaded_file)
                        document_id = ingest_pdf(
                            pdf_path,
                            reset_database=reset and file_number == 0,
                            progress_callback=update_progress,
                        )
                        st.session_state.document_ids.append(document_id)

                    progress.empty()
                    st.success(f"{len(uploaded_files)} PDF file(s) indexed successfully.")
                except Exception as e:
                    progress.empty()
                    st.error(str(e))

    indexed_documents = list_indexed_documents()
    if indexed_documents:
        st.subheader("Indexed PDFs")
        for document in indexed_documents:
            document_id = document["document_id"]
            st.write(document["source"])
            if st.button("Remove", key=f"remove_{document_id}"):
                delete_document(document_id)
                st.session_state.document_ids = [
                    active_id
                    for active_id in st.session_state.document_ids
                    if active_id != document_id
                ]
                st.rerun()

    st.subheader("Database")
    st.download_button(
        "Save database",
        data=export_database(),
        file_name="chroma-database.zip",
        mime="application/zip",
    )
    database_upload = st.file_uploader(
        "Load database archive",
        type=["zip"],
        key="database_upload",
    )
    if database_upload and st.button("Load database"):
        try:
            import_database(database_upload.getvalue())
            st.session_state.document_ids = [
                document["document_id"]
                for document in list_indexed_documents()
            ]
            st.success("Database loaded successfully.")
            st.rerun()
        except Exception as error:
            st.error(str(error))

    st.divider()

    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()

# CHAT HISTORY
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# QUESTION
question = st.chat_input("Ask a question about the PDF...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Searching PDF..."):
            try:
                if not st.session_state.document_ids:
                    raise ValueError("Process at least one PDF before asking a question.")

                result = answer_question(
                    question,
                    st.session_state.document_ids,
                )
                answer = result["answer"]
                st.markdown(answer)

                # SOURCES
                sources = result["sources"]
                if sources:
                    st.markdown("#### Sources")
                    seen = set()

                    for source in sources:
                        key = (source["source"], source["page"], source["type"])

                        if key in seen:
                            continue

                        seen.add(key)

                        st.markdown(
                            f"- "
                            f"**{source['source']}** "
                            f"— page "
                            f"**{source['page']}** "
                            f"({source['type']})"
                        )

                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )

            except Exception as e:
                error = f"Error: {e}"
                st.error(error)
