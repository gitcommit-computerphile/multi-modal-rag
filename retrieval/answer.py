from models.factory import get_vision_client
from retrieval.context_assembly import assemble_context
from retrieval.grounding import load_page_images
from retrieval.vector_search import search_chunks


def answer_question(
    question: str,
    doc_id: str | None = None,
    top_k: int = 5,
    history: list[dict] | None = None,
) -> dict:
    """End-to-end: retrieve, ground, and answer a question.

    history: prior conversation turns, each {"role": "user"|"assistant", "content": str},
    oldest first, so the model can resolve follow-up references (e.g. "what about that region").

    Returns {answer_text, citations, retrieved_chunk_ids}
    """
    # M4: Vector search
    chunks = search_chunks(question, doc_id=doc_id, top_k=top_k)
    if not chunks:
        return {
            "answer_text": "No relevant information found.",
            "citations": [],
            "retrieved_chunk_ids": [],
        }

    # M4: Assemble context with parent-page chunks
    context_chunks = assemble_context(chunks)

    # M4: Load page images for visual grounding
    page_images = load_page_images(context_chunks)

    # M4: Call VLM with context + images
    client = get_vision_client()
    result = client.answer_with_context(question, context_chunks, page_images, history=history)

    return {
        "answer_text": result.answer_text,
        "citations": result.citations,
        "retrieved_chunk_ids": [c["id"] for c in context_chunks],
    }
