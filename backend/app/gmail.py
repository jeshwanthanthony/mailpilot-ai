import base64
import re
from email.message import EmailMessage
from typing import Any

import bleach
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from app.config import Settings
from app.models import EmailSummary
from app.repository import ConnectionRepository

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose",
]

ALLOWED_TAGS = [
    "a",
    "b",
    "blockquote",
    "br",
    "code",
    "div",
    "em",
    "h1",
    "h2",
    "h3",
    "hr",
    "i",
    "li",
    "ol",
    "p",
    "pre",
    "span",
    "strong",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "u",
    "ul",
]


def create_oauth_flow(settings: Settings, state: str | None = None) -> Flow:
    if not settings.google_client_id or not settings.google_client_secret:
        raise RuntimeError("Google OAuth is not configured")
    return Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [f"{settings.base_url}/auth/google/callback"],
            }
        },
        scopes=SCOPES,
        state=state,
        redirect_uri=f"{settings.base_url}/auth/google/callback",
    )


def get_gmail_service(
    user_id: str,
    settings: Settings,
    repository: ConnectionRepository,
) -> Any:
    connection = repository.get_connection(user_id)
    if not connection:
        raise PermissionError("Gmail is not connected")
    credentials = Credentials(
        token=connection.get("access_token"),
        refresh_token=connection.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=SCOPES,
    )
    if credentials.expired:
        if not credentials.refresh_token:
            raise PermissionError("Gmail access expired. Reconnect your account")
        credentials.refresh(GoogleRequest())
        repository.update_access_token(
            user_id,
            credentials.token or "",
            credentials.expiry.isoformat() if credentials.expiry else None,
        )
    return build("gmail", "v1", credentials=credentials, cache_discovery=False)


def decode_body(data: str) -> str:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding).decode("utf-8", errors="replace")


def encode_message(message: EmailMessage) -> str:
    return base64.urlsafe_b64encode(message.as_bytes()).decode("ascii").rstrip("=")


def find_body(payload: dict[str, Any], mime_type: str) -> str:
    if not payload:
        return ""
    body = payload.get("body") or {}
    data = body.get("data")
    if payload.get("mimeType") == mime_type and data:
        return decode_body(data)
    for part in payload.get("parts") or []:
        value = find_body(part, mime_type)
        if value.strip():
            return value
    return ""


def sanitize_html(value: str) -> str:
    return bleach.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes={"a": ["href", "title"], "td": ["colspan", "rowspan"], "th": ["colspan", "rowspan"]},
        protocols=["http", "https", "mailto"],
        strip=True,
        strip_comments=True,
    )


def headers_map(message: dict[str, Any]) -> dict[str, str]:
    headers = message.get("payload", {}).get("headers", []) or []
    return {(header.get("name") or "").lower(): header.get("value") or "" for header in headers}


def extract_email_address(value: str) -> str:
    match = re.search(r"<([^>]+)>", value or "")
    if match:
        return match.group(1).strip()
    match = re.search(r"[\w.+-]+@[\w.-]+\.\w+", value or "")
    return match.group(0) if match else ""


def reply_subject(subject: str) -> str:
    value = (subject or "").strip()
    if not value:
        return "Re: (no subject)"
    return value if re.match(r"^re:\s*", value, re.IGNORECASE) else f"Re: {value}"


def summarize_message(message: dict[str, Any]) -> EmailSummary:
    headers = headers_map(message)
    labels = message.get("labelIds") or []
    return EmailSummary(
        id=message["id"],
        thread_id=message.get("threadId") or "",
        subject=headers.get("subject") or "(no subject)",
        sender=headers.get("from") or "Unknown sender",
        date=headers.get("date") or "",
        snippet=message.get("snippet") or "",
        is_unread="UNREAD" in labels,
    )


def build_reply(message: dict[str, Any], body: str) -> tuple[EmailMessage, str, str]:
    headers = headers_map(message)
    recipient = extract_email_address(headers.get("reply-to") or headers.get("from") or "")
    if not recipient:
        raise ValueError("The message does not include a reply address")
    subject = reply_subject(headers.get("subject") or "")
    reply = EmailMessage()
    reply["To"] = recipient
    reply["Subject"] = subject
    if headers.get("message-id"):
        reply["In-Reply-To"] = headers["message-id"]
        references = headers.get("references", "").strip()
        reply["References"] = f"{references} {headers['message-id']}".strip()
    reply.set_content(body.strip())
    return reply, recipient, subject
