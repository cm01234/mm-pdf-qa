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

- [ ] Improve chunking by splitting on paragraphs and preserving page or section context.
- [ ] Keep table rows together when creating chunks.
- [ ] Retrieve more candidates, then rerank or select the best context before calling Ollama.
- [ ] Add document and page context to every stored chunk.
- [ ] Improve answer validation so unsupported answers are rejected or clearly marked.

## Ingestion and User Experience

- [x] Add a progress bar showing PDF processing progress to the user.
- [ ] Avoid saving the uploaded PDF on every Streamlit rerun.
- [ ] Save uploaded files only when the user clicks **Process PDF**.
- [ ] Sanitize uploaded filenames before writing them to `documents/`.
- [ ] Display ingestion progress in the Streamlit interface instead of only printing to the terminal.
- [ ] Report the current page, extracted object count, image analysis progress, and embedding progress.
- [ ] Detect and report empty or invalid PDFs.
- [ ] Add a visible list of currently indexed documents.
- [ ] Add a button to remove one indexed document without clearing the entire database.

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

1. Add model and ChromaDB caching.
2. Add document IDs and retrieval filtering.
3. Handle empty collections and Ollama errors.
4. Improve chunking and source context.
5. Add progress reporting and document management.
6. Add tests and configuration documentation.
