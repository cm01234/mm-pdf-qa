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

- [ ] Allow using more than one PDF file.
- [x] Add a progress bar showing PDF processing progress to the user.
- [ ] Avoid saving the uploaded PDF on every Streamlit rerun.
- [ ] Save uploaded files only when the user clicks **Process PDF**.
- [ ] Sanitize uploaded filenames before writing them to `documents/`.
- [x] Display ingestion progress in the Streamlit interface instead of only printing to the terminal.
- [ ] Report the current page, extracted object count, image analysis progress, and embedding progress.
- [ ] Detect and report empty or invalid PDFs.
- [ ] Add a visible list of currently indexed documents.
- [ ] Add a button to remove one indexed document without clearing the entire database.
- [ ] Allow saving and loading databases.

## Code Quality

- [ ] Replace print-based status reporting with structured logging.
- [ ] Move configuration values such as paths, chunk size, retrieval count, and model names into environment variables.
- [ ] Add type hints to public functions.
- [ ] Break large ingestion and UI functions into smaller testable units.
- [ ] Remove unused imports and standardize formatting.

## Testing

- [x] Add tests for `chunk_text()` with empty, short, overlapping, and long text.
- [x] Test PDF text, table, and image extraction.
- [x] Test unique IDs across multiple PDFs.
- [x] Test retrieval with an empty database.
- [x] Test metadata and source page output.
- [x] Add a smoke test for the Streamlit application startup.

## Documentation and Deployment

- [ ] Document supported Python and Ollama versions.
- [ ] Add an `.env.example` file with safe default configuration.
- [ ] Document how to rebuild or clear the ChromaDB index.
- [ ] Document model memory requirements and alternative smaller Ollama models.
- [ ] Add a license and contribution guidelines if the project will be shared.

## Suggested Implementation Order

Completed:

- Model and ChromaDB caching
- Document IDs and PDF-specific retrieval filtering
- Empty collection handling and Ollama error messages
- PDF processing progress bar and Streamlit progress updates
- Regression tests for ingestion, retrieval, caching, Ollama errors, and app startup

Next:

1. Report page-level and image-analysis progress during ingestion.
2. Avoid saving uploaded PDFs on every Streamlit rerun.
3. Improve chunking and preserve section, page, and table context.
4. Add document management controls for listing and removing indexed PDFs.
5. Add retrieval reranking and answer validation.
6. Finish configuration, logging, type hints, and documentation improvements.
