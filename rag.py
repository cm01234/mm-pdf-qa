import re
from typing import Any

from database import get_collection
from llm import ask_llm
from models import get_embedding_model
from config import RETRIEVAL_COUNT

STOPWORDS = {
    "about", "after", "again", "also", "answer", "and", "are", "been",
    "from", "have", "into", "more", "only", "that", "the", "their",
    "them", "there", "these", "they", "this", "using", "was", "what",
    "when", "where", "which", "with",
}


def _answer_is_supported(answer: str, context_text: str) -> bool:

    refusal_terms = (
        "not available in the pdf",
        "could not find information",
        "cannot be determined from the pdf",
    )

    if any(term in answer.lower() for term in refusal_terms):
        return True

    answer_terms = {
        term
        for term in re.findall(r"[a-z0-9]{3,}", answer.lower())
        if term not in STOPWORDS
    }
    context_terms = set(re.findall(r"[a-z0-9]{3,}", context_text.lower()))

    return bool(answer_terms & context_terms)


def _rerank_results(
    question: str,
    results: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:

    query_terms = set(re.findall(r"[a-z0-9]{3,}", question.lower()))

    scored_results = []

    for position, result in enumerate(results):
        document_terms = set(
            re.findall(r"[a-z0-9]{3,}", result["text"].lower())
        )
        overlap = len(query_terms & document_terms)
        scored_results.append((overlap, -position, result))

    scored_results.sort(reverse=True)

    return [result for _, _, result in scored_results[:limit]]


def retrieve(
    question: str,
    document_id: str | list[str],
    k: int = RETRIEVAL_COUNT,
) -> list[dict[str, Any]]:

    collection = get_collection()

    if collection.count() == 0:
        return []

    query_embedding = get_embedding_model().encode(
        [question], normalize_embeddings=True
    )[0].tolist()

    candidate_count = max(k * 3, k)
    document_filter = (
        {"document_id": document_id}
        if isinstance(document_id, str)
        else {"document_id": {"$in": document_id}}
    )

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=candidate_count,
        where=document_filter,
    )

    documents = results.get("documents") or []
    metadatas = results.get("metadatas") or []

    if not documents or not metadatas:
        return []

    documents = documents[0] or []
    metadatas = metadatas[0] or []

    output = []

    for document, metadata in zip(documents, metadatas):

        output.append({"text": document, "metadata": metadata})

    return _rerank_results(question, output, k)


def answer_question(
    question: str,
    document_id: str | list[str],
) -> dict[str, Any]:

    results = retrieve(question, document_id)

    if not results:

        return {
            "answer": ("I could not find " "information about that " "in the PDF."),
            "sources": [],
        }

    context = []

    sources = []

    for result in results:

        metadata = result["metadata"]

        context.append(f"""
FILE: {metadata['source']}
PAGE: {metadata['page']}
TYPE: {metadata['type']}

CONTENT:
{result['text']}
""")

        sources.append(metadata)

    context_text = "\n\n".join(context)

    prompt = f"""
You are a local PDF question-answering
assistant.

Answer the user's question using ONLY
the supplied PDF context.

IMPORTANT RULES:

- Do not invent information.
- If the answer is not in the context,
  say that it is not available in the PDF.
- Cite page numbers.
- Use tables when relevant.
- Use chart/image information when relevant.
- If information comes from a chart,
  explicitly say so.
- If multiple pages are needed, combine
  them logically.
- Give a concise but complete answer.

PDF CONTEXT
===========

{context_text}


QUESTION
========

{question}
"""

    answer = ask_llm(prompt)

    if not _answer_is_supported(answer, context_text):
        answer = (
            "I could not verify that answer from the retrieved PDF context. "
            "Please ask about information contained in the PDF."
        )

    return {"answer": answer, "sources": sources}
