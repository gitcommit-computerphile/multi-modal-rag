from models.factory import get_embedding_client


def embed_chunks(chunks: list) -> list:
    """Attach embedding vectors to chunks."""
    if not chunks:
        return chunks

    client = get_embedding_client()
    texts = [c.content for c in chunks]

    embeddings = client.embed_texts(texts)

    for chunk, emb in zip(chunks, embeddings):
        chunk.embedding = emb

    return chunks
