# Local PDF CLANKER

A local PDF question-answering assistant built with Streamlit, PyMuPDF, ChromaDB, Sentence Transformers, and Ollama. Upload a PDF, index its text, tables, and images, then ask questions about its contents through a chat interface. Documents and model calls stay on your machine.

> This project is designed for local use. Ollama must be installed separately and the required model must be downloaded before asking questions.

## Features

- Extracts PDF text, tables, and embedded images
- Uses a local embedding model for semantic search
- Stores embeddings persistently in ChromaDB
- Uses Ollama for grounded question answering
- Uses a vision-capable Ollama model to describe charts, tables, diagrams, and images
- Shows source file names, page numbers, and content types with answers

## Requirements

- Python 3.10 or newer
- Ollama installed and running locally
- Enough disk space and memory for the selected embedding and language models
- Git, if you want to clone or publish the project on GitHub

The default models are:

- Embeddings: `BAAI/bge-small-en-v1.5`
- Ollama: `qwen3-vl:8b`

Pull the default Ollama model before starting the app:

```bash
ollama pull qwen3-vl:8b
```

## Setup

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install the Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Ensure Ollama is running. Depending on your installation, this may be automatic; otherwise run:

   ```bash
   ollama serve
   ```

4. Optionally create a `.env` file to override the defaults:

   ```dotenv
   OLLAMA_MODEL=qwen3-vl:8b
   EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
   ```

   Do not commit `.env`. It is ignored by `.gitignore`.

## Run

Start the Streamlit application from the project directory:

```bash
streamlit run app.py
```

Then open the local URL shown by Streamlit, usually `http://localhost:8501`.

## Usage

1. Upload a PDF from the sidebar.
2. Select **Clear existing database** if you want to replace the current ChromaDB collection.
3. Click **Process PDF** and wait for indexing to finish.
4. Ask questions in the chat input.
5. Review the listed sources and page numbers below each answer.

The first run may take longer because the embedding model must be downloaded and loaded.

## Project Structure

```text
app.py             Streamlit user interface
models.py          Cached Sentence Transformers model factory
database.py        Cached ChromaDB client and collection
ingest.py          PDF ingestion, chunking, embedding, and storage
pdf_processor.py   Text, table, and image extraction
rag.py             ChromaDB retrieval and answer generation
llm.py             Ollama text and vision model calls
requirements.txt   Python dependencies
TODO.md            Planned improvements
.streamlit/        Streamlit configuration
documents/         Uploaded PDFs (ignored)
data/chroma/       Persistent ChromaDB data (ignored)
data/images/       Extracted PDF images (ignored)
```

## Data and Resetting

Generated files are stored locally:

- Uploaded PDFs go to `documents/`.
- Extracted images go to `data/images/`.
- The ChromaDB collection is stored in `data/chroma/`.

Use the **Clear existing database** checkbox before processing a PDF when you need to rebuild the index. This removes the existing ChromaDB data before ingestion.

These folders are excluded from Git because they may contain private documents, generated data, or large local files.

## Publish on GitHub

Review the files before publishing and confirm that private PDFs, `.env`, ChromaDB data, and extracted images are ignored:

```bash
git init
git add .
git status
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repository>.git
git push -u origin main
```

Create the empty repository on GitHub first. Do not add generated data or secrets to the repository.

## Development Checks

Compile the Python modules before pushing changes:

```bash
python -m py_compile app.py ingest.py models.py pdf_processor.py rag.py llm.py
```

## Notes

- Answers are generated from retrieved PDF content and may say that information is unavailable when it is not found in the indexed context.
- Image and chart understanding requires a vision-capable Ollama model.
- The embedding model is downloaded by Sentence Transformers on first use.
- The embedding model is cached by Streamlit after it is loaded.
- Keep `.env` out of version control if it contains private configuration or credentials.
