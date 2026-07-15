from typing import Literal

from pydantic import BaseModel, Field


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
