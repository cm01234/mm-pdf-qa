from database import get_collection
from llm import ask_llm
from models import get_embedding_model


def retrieve(question, document_id, k=5):

    collection = get_collection()

    query_embedding = get_embedding_model().encode(
        [question], normalize_embeddings=True
    )[0].tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        where={"document_id": document_id},
    )

    documents = results["documents"][0]

    metadatas = results["metadatas"][0]

    output = []

    for document, metadata in zip(documents, metadatas):

        output.append({"text": document, "metadata": metadata})

    return output


def answer_question(question, document_id):

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

    return {"answer": answer, "sources": sources}
