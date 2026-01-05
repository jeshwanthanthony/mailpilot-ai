import os
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # dev only for localhost

import re
import base64
import requests
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest

from pydantic import BaseModel

from supabase import create_client


load_dotenv()

app = FastAPI()

# -------- ENV --------
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# IMPORTANT: compose is required for creating drafts / sending.
# After changing scopes, you MUST reconnect Gmail so tokens include this scope.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]
# TEMP: until you add real platform auth, we pin to you as the test user
TEST_USER_EMAIL = "jeshwanthanthony@gmail.com"


# -------- CORS --------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------- HELPERS --------
def get_or_create_user():
    res = supabase.table("users").select("*").eq("email", TEST_USER_EMAIL).execute()
    if res.data:
        return res.data[0]
    ins = supabase.table("users").insert({"email": TEST_USER_EMAIL}).execute()
    return ins.data[0]


def extract_email_address(s: str) -> str:
    """
    Extracts email from 'Name <email@domain>' or returns s if already email-ish.
    """
    if not s:
        return ""
    m = re.search(r"<([^>]+)>", s)
    if m:
        return m.group(1).strip()
    parts = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", s)
    return parts[0] if parts else s.strip()


def b64url_decode(data: str) -> bytes:
    # Gmail uses base64url without padding sometimes
    data = data.replace("-", "+").replace("_", "/")
    pad = len(data) % 4
    if pad:
        data += "=" * (4 - pad)
    return base64.b64decode(data)


def b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("utf-8").rstrip("=")


def normalize_reply_subject(subject: str) -> str:
    s = (subject or "").strip()
    if not s:
        return "Re: (no subject)"
    if re.match(r"^\s*re:\s*", s, flags=re.IGNORECASE):
        return s
    return f"Re: {s}"


def get_header(headers_map: Dict[str, str], key: str) -> str:
    if key in headers_map:
        return headers_map[key] or ""
    lk = key.lower()
    for k, v in headers_map.items():
        if (k or "").lower() == lk:
            return v or ""
    return ""


def build_reply_mime(
    to_email: str,
    subject: str,
    body_text: str,
    in_reply_to: Optional[str] = None,
    references: Optional[str] = None,
) -> str:
    """
    Build a simple text/plain MIME message for a reply.
    """
    to_email = (to_email or "").replace("\n", " ").replace("\r", " ").strip()
    subject = (subject or "").replace("\n", " ").replace("\r", " ").strip()

    lines = []
    lines.append(f"To: {to_email}")
    lines.append(f"Subject: {subject}")
    lines.append("MIME-Version: 1.0")
    lines.append('Content-Type: text/plain; charset="UTF-8"')
    lines.append("Content-Transfer-Encoding: 7bit")

    if in_reply_to:
        in_reply_to = in_reply_to.strip()
        if not in_reply_to.startswith("<"):
            in_reply_to = f"<{in_reply_to.strip('<>')}>"
        lines.append(f"In-Reply-To: {in_reply_to}")

    if references:
        references = references.strip()
        if "<" not in references:
            references = f"<{references.strip('<>')}>"
        lines.append(f"References: {references}")

    lines.append("")
    lines.append((body_text or "").strip() + "\n")

    return "\r\n".join(lines)


def get_or_refresh_creds_for_user(user_id: str) -> Credentials:
    conn_res = (
        supabase.table("gmail_connections")
        .select("*")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not conn_res.data:
        raise RuntimeError("Gmail not connected")

    conn = conn_res.data[0]

    creds = Credentials(
        token=conn.get("access_token"),
        refresh_token=conn.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=SCOPES,
    )

    # Refresh if needed
    try:
        if creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())
            supabase.table("gmail_connections").update(
                {
                    "access_token": creds.token or "",
                    "token_expiry": creds.expiry.isoformat() if creds.expiry else None,
                }
            ).eq("user_id", user_id).execute()
    except Exception:
        raise RuntimeError("Token refresh failed. Please reconnect Gmail.")

    return creds


def get_gmail_service_for_user(user_id: str):
    creds = get_or_refresh_creds_for_user(user_id)
    return build("gmail", "v1", credentials=creds)


def find_text_plain(payload: Dict[str, Any]) -> str:
    """
    Walk Gmail payload to find best text/plain body.
    """
    if not payload:
        return ""

    mime_type = payload.get("mimeType", "")
    body = payload.get("body", {}) or {}
    data = body.get("data")

    if mime_type == "text/plain" and data:
        return b64url_decode(data).decode("utf-8", errors="replace")

    parts = payload.get("parts") or []
    for p in parts:
        txt = find_text_plain(p)
        if txt.strip():
            return txt

    if mime_type == "text/html" and data:
        return b64url_decode(data).decode("utf-8", errors="replace")

    return ""


def find_text_html(payload: Dict[str, Any]) -> str:
    if not payload:
        return ""

    mime_type = payload.get("mimeType", "")
    body = payload.get("body", {}) or {}
    data = body.get("data")

    if mime_type == "text/html" and data:
        return b64url_decode(data).decode("utf-8", errors="replace")

    parts = payload.get("parts") or []
    for p in parts:
        html = find_text_html(p)
        if html.strip():
            return html

    return ""










def get_message_full(service, message_id: str) -> Dict[str, Any]:
    return (
        service.users()
        .messages()
        .get(userId="me", id=message_id, format="full")
        .execute()
    )


def get_headers_map(msg: Dict[str, Any]) -> Dict[str, str]:
    headers = msg.get("payload", {}).get("headers", []) or []
    return {h.get("name", ""): h.get("value", "") for h in headers}


def make_flow():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise RuntimeError("Missing GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET in .env")

    return Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [f"{BASE_URL}/auth/google/callback"],
            }
        },
        scopes=SCOPES,
        redirect_uri=f"{BASE_URL}/auth/google/callback",
    )


# -------- ROUTES --------
@app.get("/health")
def health():
    return {"ok": True}


@app.get("/")
def root():
    return {"ok": True, "next": "Go to /auth/google/start then /emails or use frontend /inbox"}


@app.get("/auth/google/start")
def auth_start():
    flow = make_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return RedirectResponse(auth_url)


@app.get("/auth/google/callback")
def auth_callback(request: Request):
    flow = make_flow()
    flow.fetch_token(authorization_response=str(request.url))
    creds = flow.credentials

    user = get_or_create_user()

    supabase.table("gmail_connections").delete().eq("user_id", user["id"]).execute()

    supabase.table("gmail_connections").insert(
        {
            "user_id": user["id"],
            "gmail_address": TEST_USER_EMAIL,
            "access_token": creds.token or "",
            "refresh_token": creds.refresh_token or "",
            "token_expiry": creds.expiry.isoformat() if creds.expiry else None,
        }
    ).execute()

    return RedirectResponse(FRONTEND_URL + "/inbox")


@app.get("/emails")
def list_emails(max_results: int = 20, page_token: Optional[str] = None):
    user = get_or_create_user()

    try:
        service = get_gmail_service_for_user(user["id"])
    except RuntimeError as e:
        return JSONResponse({"error": str(e)}, status_code=401)

    list_kwargs = {"userId": "me", "maxResults": max_results}
    if page_token:
        list_kwargs["pageToken"] = page_token

    results = service.users().messages().list(**list_kwargs).execute()
    messages = results.get("messages", [])
    next_page_token = results.get("nextPageToken")

    out = []
    for m in messages:
        msg = service.users().messages().get(
            userId="me",
            id=m["id"],
            format="metadata",
            metadataHeaders=["Subject", "From", "Date"],
        ).execute()

        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        out.append(
            {
                "id": msg["id"],
                "threadId": msg.get("threadId"),
                "subject": headers.get("Subject", ""),
                "from": headers.get("From", ""),
                "date": headers.get("Date", ""),
                "snippet": msg.get("snippet", ""),
            }
        )

    return {"emails": out, "next_page_token": next_page_token}



@app.get("/emails/{message_id}/body")
def get_email_body(message_id: str):
    user = get_or_create_user()

    try:
        service = get_gmail_service_for_user(user["id"])
    except RuntimeError as e:
        return JSONResponse({"error": str(e)}, status_code=401)

    try:
        msg = get_message_full(service, message_id)
    except Exception as e:
        return JSONResponse({"error": f"Failed to fetch email: {str(e)}"}, status_code=500)

    payload = msg.get("payload", {}) or {}

    # Prefer HTML for “exact” rendering
    html = find_text_html(payload).strip()
    if html:
        return {"format": "html", "body": html}

    # Fallback to plain
    plain = find_text_plain(payload).strip()
    if plain:
        return {"format": "plain", "body": plain}

    # Last resort
    return {"format": "plain", "body": (msg.get("snippet") or "").strip()}



class DraftReplyRequest(BaseModel):
    tone: Optional[str] = "professional"
    extra_instructions: Optional[str] = None


@app.post("/emails/{message_id}/draft-reply")
def draft_reply(message_id: str, body: DraftReplyRequest):
    if not OPENAI_API_KEY:
        return JSONResponse({"error": "Missing OPENAI_API_KEY in backend .env"}, status_code=500)

    user = get_or_create_user()

    try:
        service = get_gmail_service_for_user(user["id"])
    except RuntimeError as e:
        return JSONResponse({"error": str(e)}, status_code=401)

    msg = get_message_full(service, message_id)
    headers = get_headers_map(msg)

    subject = get_header(headers, "Subject")
    from_raw = get_header(headers, "From")
    to_raw = get_header(headers, "To")
    reply_to_raw = get_header(headers, "Reply-To")

    from_email = extract_email_address(from_raw)
    to_email = extract_email_address(to_raw)
    reply_to_email = extract_email_address(reply_to_raw) if reply_to_raw else from_email

    email_body = find_text_plain(msg.get("payload", {})).strip()
    if not email_body:
        email_body = msg.get("snippet", "") or ""

    tone = (body.tone or "professional").strip()
    extra = (body.extra_instructions or "").strip()

    system = (
        "You write concise, correct email replies. "
        "Be helpful and polite. Keep it short unless asked for detail."
    )

    user_prompt = f"""
Write an email reply.

Tone: {tone}
From: {from_raw}
To: {to_raw}
Subject: {subject}

Original email:
{email_body}

{("Extra instructions: " + extra) if extra else ""}
Return ONLY the email reply body text (no subject line).
""".strip()

    try:
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.4,
            },
            timeout=60,
        )
        data = r.json()
        if r.status_code >= 400:
            return JSONResponse({"error": data}, status_code=500)

        draft_text = (data["choices"][0]["message"]["content"] or "").strip()
    except Exception as e:
        return JSONResponse({"error": f"OpenAI request failed: {str(e)}"}, status_code=500)

    return {
        "message_id": message_id,
        "subject": subject,
        "reply_to_email": reply_to_email,
        "original_to_email": to_email,
        "draft_text": draft_text,
    }


class SendReplyRequest(BaseModel):
    draft_text: str


@app.post("/emails/{message_id}/send")
def send_reply(message_id: str, body: SendReplyRequest):
    user = get_or_create_user()

    try:
        service = get_gmail_service_for_user(user["id"])
    except RuntimeError as e:
        return JSONResponse({"error": str(e)}, status_code=401)

    msg = get_message_full(service, message_id)
    headers = get_headers_map(msg)

    subject_raw = get_header(headers, "Subject")
    from_raw = get_header(headers, "From")
    to_raw = get_header(headers, "To")
    reply_to_raw = get_header(headers, "Reply-To")
    message_id_hdr = get_header(headers, "Message-ID")
    references_hdr = get_header(headers, "References")

    from_email = extract_email_address(from_raw)
    reply_to_email = extract_email_address(reply_to_raw) if reply_to_raw else from_email

    if not reply_to_email:
        return JSONResponse(
            {"error": "Could not determine recipient (Reply-To/From missing)."},
            status_code=400,
        )

    thread_id = msg.get("threadId")
    if not thread_id:
        return JSONResponse(
            {"error": "Missing threadId on message; cannot send threaded reply."},
            status_code=500,
        )

    reply_subject = normalize_reply_subject(subject_raw)

    draft_text = (body.draft_text or "").strip()
    if not draft_text:
        return JSONResponse({"error": "draft_text is required."}, status_code=400)

    in_reply_to = message_id_hdr or None

    references = references_hdr or message_id_hdr or None
    if references_hdr and message_id_hdr and message_id_hdr not in references_hdr:
        references = (references_hdr.strip() + " " + message_id_hdr.strip()).strip()

    mime = build_reply_mime(
        to_email=reply_to_email,
        subject=reply_subject,
        body_text=draft_text,
        in_reply_to=in_reply_to,
        references=references,
    )

    raw = b64url_encode(mime.encode("utf-8"))

    try:
        sent = service.users().messages().send(
            userId="me",
            body={
                "raw": raw,
                "threadId": thread_id,
            },
        ).execute()
    except Exception as e:
        return JSONResponse({"error": f"Failed to send via Gmail API: {str(e)}"}, status_code=500)

    return {
        "ok": True,
        "sent_id": sent.get("id"),
        "threadId": sent.get("threadId"),
        "to": reply_to_email,
        "subject": reply_subject,
        "original_to": extract_email_address(to_raw),
    }
