from db.session import get_session
from models.factory import get_embedding_client


def search_chunks(query: str, doc_id: str | None = None, top_k: int = 5) -> list:
    """Embed query and find top-k similar chunks via pgvector."""
    client = get_embedding_client()
    query_embedding = client.embed_query(query)

    session = get_session()
    from db.models import Chunk

    # Build base query
    q = session.query(Chunk).order_by(
        Chunk.embedding.cosine_distance(query_embedding)
    )

    if doc_id:
        q = q.filter(Chunk.document_id == doc_id)

    results = q.limit(top_k).all()
    session.close()

    return results
