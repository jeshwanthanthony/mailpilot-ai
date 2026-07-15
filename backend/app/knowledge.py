from __future__ import annotations

import re
from uuid import UUID

from app.ai import EmbeddingWriter
from app.config import Settings
from app.models import KnowledgeCitation, KnowledgeDocument, KnowledgeDocumentCreate
from app.repository import ConnectionRepository


def chunk_text(content: str, target_size: int = 900, overlap: int = 120) -> list[str]:
    normalized = re.sub(r"\r\n?", "\n", content).strip()
    if not normalized:
        return []
    paragraphs = [part.strip() for part in re.split(r"\n{2,}", normalized) if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > target_size:
            if current:
                chunks.append(current)
                current = ""
            start = 0
            while start < len(paragraph):
                end = min(start + target_size, len(paragraph))
                chunks.append(paragraph[start:end].strip())
                if end == len(paragraph):
                    break
                start = max(end - overlap, start + 1)
            continue
        candidate = f"{current}\n\n{paragraph}".strip()
        if current and len(candidate) > target_size:
            chunks.append(current)
            tail = current[-overlap:].lstrip()
            current = f"{tail}\n\n{paragraph}".strip() if tail else paragraph
        else:
            current = candidate
    if current:
        chunks.append(current)
    return [chunk for chunk in chunks if chunk]


class KnowledgeService:
    def __init__(
        self,
        settings: Settings,
        repository: ConnectionRepository,
        embeddings: EmbeddingWriter,
    ) -> None:
        self.settings = settings
        self.repository = repository
        self.embeddings = embeddings

    def ingest(self, user_id: str, document: KnowledgeDocumentCreate) -> KnowledgeDocument:
        chunks = chunk_text(document.content)
        vectors = self.embeddings.embed(chunks)
        if len(vectors) != len(chunks):
            raise RuntimeError("Embedding response did not match the submitted document")
        stored = self.repository.create_knowledge_document(
            user_id=user_id,
            title=document.title.strip(),
            source_url=str(document.source_url) if document.source_url else None,
            chunks=list(zip(chunks, vectors, strict=True)),
        )
        return KnowledgeDocument.model_validate(stored)

    def list(self, user_id: str) -> list[KnowledgeDocument]:
        return [
            KnowledgeDocument.model_validate(item)
            for item in self.repository.list_knowledge_documents(user_id)
        ]

    def delete(self, user_id: str, document_id: UUID) -> bool:
        return self.repository.delete_knowledge_document(user_id, document_id)

    def search(self, user_id: str, query: str) -> list[KnowledgeCitation]:
        embedding = self.embeddings.embed([query])[0]
        matches = self.repository.search_knowledge(
            user_id=user_id,
            embedding=embedding,
            threshold=self.settings.rag_match_threshold,
            limit=self.settings.rag_max_chunks,
        )
        return [KnowledgeCitation.model_validate(item) for item in matches]
