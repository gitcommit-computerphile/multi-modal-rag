from abc import ABC, abstractmethod
from dataclasses import dataclass
import base64

import anthropic
from openai import OpenAI


@dataclass
class AnswerResult:
    answer_text: str
    citations: list[dict]


class VisionModelClient(ABC):
    @abstractmethod
    def describe_table(self, image_bytes: bytes, context: str | None = None) -> str:
        """Return markdown table transcription from an image."""
        pass

    @abstractmethod
    def describe_figure(self, image_bytes: bytes, context: str | None = None) -> str:
        """Return structured description of a chart/figure, including data values."""
        pass

    @abstractmethod
    def answer_with_context(
        self,
        question: str,
        text_chunks: list[dict],
        page_images: list[dict],
        history: list[dict] | None = None,
    ) -> AnswerResult:
        """Answer a question given text chunks and page images, return answer + citations.

        history: prior turns in the conversation, each {"role": "user"|"assistant", "content": str},
        oldest first. Used so follow-up questions can refer back to earlier turns.
        """
        pass


class AnthropicVisionClient(VisionModelClient):
    def __init__(self, model: str = "claude-sonnet-5", api_key: str = ""):
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key or None)

    def describe_table(self, image_bytes: bytes, context: str | None = None) -> str:
        """Transcribe a table image to markdown."""
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_bytes.hex(),
                        },
                    },
                    {
                        "type": "text",
                        "text": "Convert this table image to valid markdown. Include all rows and columns, preserving headers. Output ONLY the markdown table.",
                    },
                ],
            }
        ]
        resp = self.client.messages.create(
            model=self.model, max_tokens=2000, messages=messages
        )
        return resp.content[0].text

    def describe_figure(self, image_bytes: bytes, context: str | None = None) -> str:
        """Describe a chart/figure, extracting axes, labels, and data values."""
        prompt = "Describe this chart/figure precisely. Include: axis labels, title, legend, and all data values/percentages shown. Be literal and complete."
        if context:
            prompt += f"\nContext: {context}"

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_bytes.hex(),
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ]
        resp = self.client.messages.create(
            model=self.model, max_tokens=1500, messages=messages
        )
        return resp.content[0].text

    def answer_with_context(
        self,
        question: str,
        text_chunks: list[dict],
        page_images: list[dict],
        history: list[dict] | None = None,
    ) -> AnswerResult:
        """Answer a question given retrieved text chunks and page images."""
        context_text = "\n\n".join(
            [f"[Chunk {i}]\n{c['content']}" for i, c in enumerate(text_chunks)]
        )

        content = [
            {
                "type": "text",
                "text": f"Answer the following question using the provided context and images.\n\nQuestion: {question}\n\nContext:\n{context_text}\n\nProvide a clear, detailed answer citing which chunks (e.g., [Chunk 0]) support your answer.",
            }
        ]

        for page_img in page_images[:3]:  # limit to first 3 images to avoid token bloat
            if "image_bytes" in page_img:
                content.append(
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": page_img["image_bytes"].hex(),
                        },
                    }
                )

        messages = [
            {"role": turn["role"], "content": turn["content"]} for turn in (history or [])
        ]
        messages.append({"role": "user", "content": content})

        resp = self.client.messages.create(
            model=self.model, max_tokens=2000, messages=messages
        )

        answer_text = resp.content[0].text
        citations = [{"chunk_id": c["id"], "page_number": c["page_number"]} for c in text_chunks]

        return AnswerResult(answer_text=answer_text, citations=citations)


class OpenAIVisionClient(VisionModelClient):
    def __init__(self, model: str = "gpt-5.4-mini", api_key: str = ""):
        self.model = model
        self.client = OpenAI(api_key=api_key or None)

    def describe_table(self, image_bytes: bytes, context: str | None = None) -> str:
        """Transcribe a table image to markdown."""
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64_image}"},
                    },
                    {
                        "type": "text",
                        "text": "Convert this table image to valid markdown. Include all rows and columns, preserving headers. Output ONLY the markdown table.",
                    },
                ],
            }
        ]
        resp = self.client.chat.completions.create(
            model=self.model, max_completion_tokens=2000, messages=messages
        )
        return resp.choices[0].message.content

    def describe_figure(self, image_bytes: bytes, context: str | None = None) -> str:
        """Describe a chart/figure, extracting axes, labels, and data values."""
        prompt = "Describe this chart/figure precisely. Include: axis labels, title, legend, and all data values/percentages shown. Be literal and complete."
        if context:
            prompt += f"\nContext: {context}"

        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64_image}"},
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ]
        resp = self.client.chat.completions.create(
            model=self.model, max_completion_tokens=1500, messages=messages
        )
        return resp.choices[0].message.content

    def answer_with_context(
        self,
        question: str,
        text_chunks: list[dict],
        page_images: list[dict],
        history: list[dict] | None = None,
    ) -> AnswerResult:
        """Answer a question given retrieved text chunks and page images."""
        context_text = "\n\n".join(
            [f"[Chunk {i}]\n{c['content']}" for i, c in enumerate(text_chunks)]
        )

        content = [
            {
                "type": "text",
                "text": f"Answer the following question using the provided context and images.\n\nQuestion: {question}\n\nContext:\n{context_text}\n\nProvide a clear, detailed answer citing which chunks (e.g., [Chunk 0]) support your answer.",
            }
        ]

        for page_img in page_images[:3]:  # limit to first 3 images
            if "image_bytes" in page_img:
                b64 = base64.b64encode(page_img["image_bytes"]).decode("utf-8")
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64}"},
                    }
                )

        messages = [
            {"role": turn["role"], "content": turn["content"]} for turn in (history or [])
        ]
        messages.append({"role": "user", "content": content})

        resp = self.client.chat.completions.create(
            model=self.model, max_completion_tokens=2000, messages=messages
        )

        answer_text = resp.choices[0].message.content
        citations = [{"chunk_id": c["id"], "page_number": c["page_number"]} for c in text_chunks]

        return AnswerResult(answer_text=answer_text, citations=citations)
