from fastapi import APIRouter

from api.schemas import QueryRequest, QueryResponse
from retrieval.answer import answer_question

router = APIRouter(prefix="/query", tags=["retrieval"])


@router.post("", response_model=QueryResponse)
async def query_documents(req: QueryRequest):
    """Answer a question by searching documents."""
    result = answer_question(
        question=req.question, doc_id=req.document_id, top_k=req.top_k
    )

    return QueryResponse(
        answer_text=result["answer_text"],
        citations=result["citations"],
        retrieved_chunk_ids=result["retrieved_chunk_ids"],
    )
