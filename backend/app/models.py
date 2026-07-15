from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, StringConstraints

KnowledgeTitle = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
KnowledgeContent = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=20, max_length=50_000),
]


class ConnectionStatus(BaseModel):
    connected: bool
    email: str | None = None
    demo_available: bool = True


class EmailSummary(BaseModel):
    id: str
    thread_id: str
    subject: str
    sender: str
    date: str
    snippet: str
    is_unread: bool
    priority: Literal["urgent", "high", "normal", "low"] | None = None
    priority_score: int | None = Field(default=None, ge=0, le=100)
    priority_signals: list[str] = Field(default_factory=list)


class EmailPage(BaseModel):
    emails: list[EmailSummary]
    next_page_token: str | None = None


class EmailBody(BaseModel):
    format: Literal["html", "plain"]
    body: str


class EmailAction(BaseModel):
    is_read: bool | None = None
    archive: bool = False


class DraftReplyRequest(BaseModel):
    tone: Literal["concise", "friendly", "professional"] = "professional"
    extra_instructions: str = Field(default="", max_length=500)


class DraftReplyResponse(BaseModel):
    message_id: str
    subject: str
    reply_to_email: str
    draft_text: str
    sources: list["KnowledgeCitation"] = Field(default_factory=list)


class SendReplyRequest(BaseModel):
    draft_text: str = Field(min_length=1, max_length=20_000)


class SendReplyResponse(BaseModel):
    ok: bool
    sent_id: str | None
    thread_id: str | None
    to: str
    subject: str


class ActionResponse(BaseModel):
    ok: bool


class KnowledgeDocumentCreate(BaseModel):
    title: KnowledgeTitle
    content: KnowledgeContent
    source_url: HttpUrl | None = None


class KnowledgeDocument(BaseModel):
    id: UUID
    title: str
    source_url: HttpUrl | None = None
    chunk_count: int = Field(ge=0)
    created_at: datetime


class KnowledgeCitation(BaseModel):
    document_id: UUID
    title: str
    source_url: HttpUrl | None = None
    content: str
    similarity: float = Field(ge=0, le=1)


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=2_000)


class KnowledgeSearchResponse(BaseModel):
    matches: list[KnowledgeCitation]
