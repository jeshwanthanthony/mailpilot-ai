from datetime import UTC, datetime
from uuid import uuid4

from app.config import Settings
from app.knowledge import KnowledgeService, chunk_text
from app.models import KnowledgeDocumentCreate


def test_chunk_text_splits_large_content_with_bounded_chunks() -> None:
    content = "First policy paragraph.\n\n" + ("Detailed guidance. " * 140)

    chunks = chunk_text(content, target_size=300, overlap=40)

    assert len(chunks) > 2
    assert all(1 <= len(chunk) <= 340 for chunk in chunks)
    assert chunks[0] == "First policy paragraph."


def test_knowledge_ingestion_embeds_and_stores_every_chunk() -> None:
    document_id = uuid4()

    class FakeEmbeddings:
        inputs: list[str] = []

        def embed(self, inputs: list[str]) -> list[list[float]]:
            self.inputs = inputs
            return [[float(index), 0.5] for index, _ in enumerate(inputs)]

    class FakeRepository:
        stored_chunks: list[tuple[str, list[float]]] = []

        def create_knowledge_document(
            self,
            user_id: str,
            title: str,
            source_url: str | None,
            chunks: list[tuple[str, list[float]]],
        ) -> dict[str, object]:
            self.stored_chunks = chunks
            return {
                "id": document_id,
                "title": title,
                "source_url": source_url,
                "chunk_count": len(chunks),
                "created_at": datetime.now(UTC),
            }

    embeddings = FakeEmbeddings()
    repository = FakeRepository()
    service = KnowledgeService(Settings(), repository, embeddings)  # type: ignore[arg-type]

    stored = service.ingest(
        "user-1",
        KnowledgeDocumentCreate(
            title="  Product handbook  ",
            content="This is verified product guidance with enough detail to index.",
        ),
    )

    assert stored.id == document_id
    assert stored.title == "Product handbook"
    assert embeddings.inputs
    assert len(repository.stored_chunks) == len(embeddings.inputs)
