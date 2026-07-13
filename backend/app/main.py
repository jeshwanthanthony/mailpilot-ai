import logging
import os
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from starlette.middleware.sessions import SessionMiddleware

from app.ai import ReplyWriter
from app.config import get_settings
from app.gmail import (
    build_reply,
    create_oauth_flow,
    encode_message,
    extract_email_address,
    find_body,
    get_gmail_service,
    headers_map,
    sanitize_html,
    summarize_message,
)
from app.models import (
    ActionResponse,
    ConnectionStatus,
    DraftReplyRequest,
    DraftReplyResponse,
    EmailAction,
    EmailBody,
    EmailPage,
    SendReplyRequest,
    SendReplyResponse,
)
from app.repository import ConnectionRepository

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("mailpilot")
settings = get_settings()
repository = ConnectionRepository(settings)
reply_writer = ReplyWriter(settings)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Gmail triage and assisted reply API",
)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    same_site="lax",
    https_only=settings.secure_cookies,
    max_age=60 * 60 * 24 * 7,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type"],
)


def require_user(request: Request) -> str:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Connect Gmail to continue")
    return str(user_id)


def service_for(request: Request) -> Any:
    try:
        return get_gmail_service(require_user(request), settings, repository)
    except PermissionError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


def full_message(service: Any, message_id: str) -> dict[str, Any]:
    try:
        return service.users().messages().get(userId="me", id=message_id, format="full").execute()
    except HttpError as error:
        status = error.resp.status if error.resp else 502
        if status == 404:
            raise HTTPException(status_code=404, detail="Email not found") from error
        logger.exception("Gmail request failed")
        raise HTTPException(status_code=502, detail="Gmail could not complete the request") from error


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "version": app.version,
        "integrations": {"gmail": settings.gmail_ready, "openai": bool(settings.openai_api_key)},
    }


@app.get("/")
def root() -> dict[str, str]:
    return {"name": settings.app_name, "docs": "/docs", "health": "/health"}


@app.get("/auth/status", response_model=ConnectionStatus)
def auth_status(request: Request) -> ConnectionStatus:
    user_id = request.session.get("user_id")
    if not user_id:
        return ConnectionStatus(connected=False)
    try:
        connection = repository.get_connection(str(user_id))
    except RuntimeError:
        return ConnectionStatus(connected=False)
    return ConnectionStatus(
        connected=bool(connection),
        email=connection.get("gmail_address") if connection else None,
    )


@app.get("/auth/google/start")
def auth_start(request: Request) -> RedirectResponse:
    if not settings.gmail_ready:
        raise HTTPException(status_code=503, detail="Gmail integration is not configured")
    flow = create_oauth_flow(settings)
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    request.session["oauth_state"] = state
    return RedirectResponse(authorization_url)


@app.get("/auth/google/callback")
def auth_callback(request: Request) -> RedirectResponse:
    expected_state = request.session.pop("oauth_state", None)
    returned_state = request.query_params.get("state")
    if not expected_state or returned_state != expected_state:
        raise HTTPException(status_code=400, detail="OAuth state validation failed")
    flow = create_oauth_flow(settings, state=expected_state)
    try:
        flow.fetch_token(authorization_response=str(request.url))
        gmail = build("gmail", "v1", credentials=flow.credentials, cache_discovery=False)
        profile = gmail.users().getProfile(userId="me").execute()
        email = profile["emailAddress"]
        user = repository.upsert_user(email)
        repository.save_connection(str(user["id"]), email, flow.credentials)
    except Exception as error:
        logger.exception("OAuth callback failed")
        raise HTTPException(status_code=502, detail="Could not connect the Gmail account") from error
    request.session["user_id"] = str(user["id"])
    return RedirectResponse(f"{settings.frontend_url.rstrip('/')}/inbox")


@app.post("/auth/logout", response_model=ActionResponse)
def logout(request: Request) -> ActionResponse:
    request.session.clear()
    return ActionResponse(ok=True)


@app.get("/emails", response_model=EmailPage)
def list_emails(
    request: Request,
    max_results: int = Query(default=25, ge=1, le=50),
    page_token: str | None = None,
    query: str | None = Query(default=None, max_length=200),
) -> EmailPage:
    service = service_for(request)
    arguments: dict[str, Any] = {"userId": "me", "maxResults": max_results, "labelIds": ["INBOX"]}
    if page_token:
        arguments["pageToken"] = page_token
    if query:
        arguments["q"] = query
    try:
        result = service.users().messages().list(**arguments).execute()
        emails = []
        for item in result.get("messages") or []:
            message = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=item["id"],
                    format="metadata",
                    metadataHeaders=["Subject", "From", "Date"],
                )
                .execute()
            )
            emails.append(summarize_message(message))
    except HttpError as error:
        logger.exception("Inbox fetch failed")
        raise HTTPException(status_code=502, detail="Gmail could not load the inbox") from error
    return EmailPage(emails=emails, next_page_token=result.get("nextPageToken"))


@app.get("/emails/{message_id}/body", response_model=EmailBody)
def get_email_body(request: Request, message_id: str) -> EmailBody:
    message = full_message(service_for(request), message_id)
    payload = message.get("payload") or {}
    html = find_body(payload, "text/html").strip()
    if html:
        return EmailBody(format="html", body=sanitize_html(html))
    plain = find_body(payload, "text/plain").strip()
    return EmailBody(format="plain", body=plain or (message.get("snippet") or "").strip())


@app.patch("/emails/{message_id}", response_model=ActionResponse)
def update_email(request: Request, message_id: str, action: EmailAction) -> ActionResponse:
    add_labels: list[str] = []
    remove_labels: list[str] = []
    if action.is_read is True:
        remove_labels.append("UNREAD")
    if action.is_read is False:
        add_labels.append("UNREAD")
    if action.archive:
        remove_labels.append("INBOX")
    if not add_labels and not remove_labels:
        return ActionResponse(ok=True)
    try:
        (
            service_for(request)
            .users()
            .messages()
            .modify(
                userId="me",
                id=message_id,
                body={"addLabelIds": add_labels, "removeLabelIds": remove_labels},
            )
            .execute()
        )
    except HttpError as error:
        logger.exception("Message update failed")
        raise HTTPException(status_code=502, detail="Gmail could not update the email") from error
    return ActionResponse(ok=True)


@app.post("/emails/{message_id}/draft-reply", response_model=DraftReplyResponse)
def draft_reply(
    request: Request,
    message_id: str,
    body: DraftReplyRequest,
) -> DraftReplyResponse:
    message = full_message(service_for(request), message_id)
    headers = headers_map(message)
    email_body = find_body(message.get("payload") or {}, "text/plain").strip()
    if not email_body:
        email_body = message.get("snippet") or ""
    try:
        draft = reply_writer.generate(
            sender=headers.get("from") or "",
            subject=headers.get("subject") or "",
            email_body=email_body,
            tone=body.tone,
            extra_instructions=body.extra_instructions.strip(),
        )
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        logger.exception("Draft generation failed")
        raise HTTPException(status_code=502, detail="Could not generate a reply") from error
    recipient = extract_email_address(headers.get("reply-to") or headers.get("from") or "")
    return DraftReplyResponse(
        message_id=message_id,
        subject=headers.get("subject") or "(no subject)",
        reply_to_email=recipient,
        draft_text=draft,
    )


@app.post("/emails/{message_id}/send", response_model=SendReplyResponse)
def send_reply(
    request: Request,
    message_id: str,
    body: SendReplyRequest,
) -> SendReplyResponse:
    service = service_for(request)
    source = full_message(service, message_id)
    thread_id = source.get("threadId")
    if not thread_id:
        raise HTTPException(status_code=422, detail="The email is missing its thread identifier")
    try:
        reply, recipient, subject = build_reply(source, body.draft_text)
        sent = (
            service.users()
            .messages()
            .send(userId="me", body={"raw": encode_message(reply), "threadId": thread_id})
            .execute()
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except HttpError as error:
        logger.exception("Reply send failed")
        raise HTTPException(status_code=502, detail="Gmail could not send the reply") from error
    return SendReplyResponse(
        ok=True,
        sent_id=sent.get("id"),
        thread_id=sent.get("threadId"),
        to=recipient,
        subject=subject,
    )
