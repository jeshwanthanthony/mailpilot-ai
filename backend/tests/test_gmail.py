import base64

from app.gmail import (
    build_reply,
    decode_body,
    encode_message,
    extract_email_address,
    find_body,
    reply_subject,
    sanitize_html,
    summarize_message,
)


def test_base64_round_trip() -> None:
    source = "A reply with punctuation: thanks!"
    encoded = base64.urlsafe_b64encode(source.encode()).decode().rstrip("=")
    assert decode_body(encoded) == source


def test_finds_nested_plain_text() -> None:
    encoded = base64.urlsafe_b64encode(b"Nested message").decode()
    payload = {
        "mimeType": "multipart/alternative",
        "parts": [{"mimeType": "text/plain", "body": {"data": encoded}}],
    }
    assert find_body(payload, "text/plain") == "Nested message"


def test_sanitizes_active_email_content() -> None:
    value = '<p>Hello</p><script>alert(1)</script><img src="https://tracker.test/pixel">'
    cleaned = sanitize_html(value)
    assert "<script" not in cleaned
    assert "<img" not in cleaned
    assert "Hello" in cleaned


def test_extracts_email_and_normalizes_subject() -> None:
    assert extract_email_address("Alex Smith <alex@example.com>") == "alex@example.com"
    assert reply_subject("Quarterly update") == "Re: Quarterly update"
    assert reply_subject("RE: Quarterly update") == "RE: Quarterly update"


def test_summarizes_unread_message() -> None:
    message = {
        "id": "message-1",
        "threadId": "thread-1",
        "labelIds": ["INBOX", "UNREAD"],
        "snippet": "Can we meet tomorrow?",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Project review"},
                {"name": "From", "value": "Alex <alex@example.com>"},
                {"name": "Date", "value": "Mon, 13 Jul 2026 10:00:00 -0400"},
            ]
        },
    }
    summary = summarize_message(message)
    assert summary.subject == "Project review"
    assert summary.is_unread is True


def test_builds_threaded_reply() -> None:
    source = {
        "payload": {
            "headers": [
                {"name": "From", "value": "Alex <alex@example.com>"},
                {"name": "Subject", "value": "Project review"},
                {"name": "Message-ID", "value": "<original@example.com>"},
            ]
        }
    }
    message, recipient, subject = build_reply(source, "Tuesday works for me.")
    raw = encode_message(message)
    assert recipient == "alex@example.com"
    assert subject == "Re: Project review"
    assert message["In-Reply-To"] == "<original@example.com>"
    assert base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4))
