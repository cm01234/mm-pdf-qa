import os

import streamlit as st

from ingest import ingest_pdf
from rag import answer_question

st.set_page_config(page_title="Local PDF CLANKER", layout="wide")

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
if "document_id" not in st.session_state:
    st.session_state.document_id = None

# SIDEBAR
with st.sidebar:
    st.header("PDF")
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded_file:
        os.makedirs("documents", exist_ok=True)
        pdf_path = os.path.join("documents", uploaded_file.name)

        with open(pdf_path, "wb") as file:
            file.write(uploaded_file.getbuffer())
        st.success(uploaded_file.name)
        reset = st.checkbox("Clear existing database")

        if st.button("Process PDF", type="primary"):
            with st.spinner("Processing PDF..."):
                try:
                    st.session_state.document_id = None

                    progress = st.progress(0, text="Starting PDF processing...")

                    def update_progress(value, message):
                        progress.progress(value, text=message)

                    st.session_state.document_id = ingest_pdf(
                        pdf_path,
                        reset_database=reset,
                        progress_callback=update_progress,
                    )
                    progress.empty()
                    st.success("PDF indexed successfully.")
                except Exception as e:
                    progress.empty()
                    st.error(str(e))

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
                if not st.session_state.document_id:
                    raise ValueError("Process a PDF before asking a question.")

                result = answer_question(
                    question,
                    st.session_state.document_id,
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
