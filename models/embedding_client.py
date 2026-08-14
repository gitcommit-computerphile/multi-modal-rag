from abc import ABC, abstractmethod

from openai import OpenAI


class EmbeddingClient(ABC):
    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts."""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string."""
        pass


class OpenAIEmbeddingClient(EmbeddingClient):
    def __init__(self, model: str = "text-embedding-3-small", api_key: str = ""):
        self.model = model
        self.client = OpenAI(api_key=api_key or None)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts using OpenAI."""
        if not texts:
            return []
        resp = self.client.embeddings.create(input=texts, model=self.model)
        return [item.embedding for item in resp.data]

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query."""
        resp = self.client.embeddings.create(input=text, model=self.model)
        return resp.data[0].embedding
