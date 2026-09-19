# Project TODO

## High Priority

- [x] Cache the Sentence Transformers model with Streamlit `st.cache_resource`.
- [x] Cache the ChromaDB client and collection to avoid recreating them on reruns.
- [x] Add a document ID or filename to Chroma metadata.
- [x] Filter retrieval to the currently selected PDF.
- [x] Prevent duplicate document IDs when indexing multiple PDFs.
- [x] Handle empty Chroma collections safely before querying results.
- [x] Show clear errors when Ollama is unavailable or the configured model is missing.

## Retrieval Quality

- [x] Improve chunking by splitting on paragraphs and preserving page or section context.
- [x] Keep table rows together when creating chunks.
- [x] Retrieve more candidates, then rerank or select the best context before calling Ollama.
- [x] Add document and page context to every stored chunk.
- [x] Improve answer validation so unsupported answers are rejected or clearly marked.

## Ingestion and User Experience

- [x] Allow using more than one PDF file.
- [x] Add a progress bar showing PDF processing progress to the user.
- [x] Avoid saving the uploaded PDF on every Streamlit rerun.
- [x] Save uploaded files only when the user clicks **Process PDF**.
- [x] Sanitize uploaded filenames before writing them to `documents/`.
- [x] Display ingestion progress in the Streamlit interface instead of only printing to the terminal.
- [x] Report the current page, extracted object count, image analysis progress, and embedding progress.
- [x] Detect and report empty or invalid PDFs.
- [x] Add a visible list of currently indexed documents.
- [x] Add a button to remove one indexed document without clearing the entire database.
- [x] Allow saving and loading databases.

## Code Quality

- [x] Replace print-based status reporting with structured logging.
- [x] Move configuration values such as paths, chunk size, retrieval count, and model names into environment variables.
- [x] Add type hints to public functions.
- [x] Break large ingestion and UI functions into smaller testable units.
- [x] Remove unused imports and standardize formatting.

## Testing

- [x] Add tests for `chunk_text()` with empty, short, overlapping, and long text.
- [x] Test PDF text, table, and image extraction.
- [x] Test unique IDs across multiple PDFs.
- [x] Test retrieval with an empty database.
- [x] Test metadata and source page output.
- [x] Add a smoke test for the Streamlit application startup.

## Documentation and Deployment

- [x] Document supported Python and Ollama versions.
- [x] Add an `.env.example` file with safe default configuration.
- [x] Document how to rebuild or clear the ChromaDB index.
- [x] Document model memory requirements and alternative smaller Ollama models.
- [x] Decide not to create a license file; contribution guidelines remain available.

## Suggested Implementation Order

Completed:

- Model and ChromaDB caching
- Document IDs and PDF-specific retrieval filtering
- Empty collection handling and Ollama error messages
- PDF processing progress bar and Streamlit progress updates
- Paragraph-aware and table-row-aware chunking
- Candidate expansion, retrieval reranking, and answer validation
- Multiple PDF indexing and document management controls
- Database save/load, filename sanitization, and empty/invalid PDF detection
- Upload/archive limits, localhost defaults, and dependency auditing
- Environment-backed configuration, logging, type hints, and ingestion refactoring
- Regression tests for ingestion, retrieval, caching, Ollama errors, and app startup

Next:

- No remaining planned items.
