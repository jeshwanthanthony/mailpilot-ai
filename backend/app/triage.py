import logging

import httpx

from app.config import Settings
from app.models import EmailSummary

logger = logging.getLogger("mailpilot.triage")


class TriageClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def enrich(self, emails: list[EmailSummary]) -> list[EmailSummary]:
        if not self.settings.triage_service_url or not emails:
            return emails
        payload = {
            "messages": [
                {
                    "id": email.id,
                    "subject": email.subject,
                    "sender": email.sender,
                    "snippet": email.snippet,
                    "unread": email.is_unread,
                }
                for email in emails
            ]
        }
        try:
            response = httpx.post(
                f"{self.settings.triage_service_url.rstrip('/')}/api/v1/triage/score-batch",
                json=payload,
                timeout=self.settings.triage_timeout_seconds,
            )
            response.raise_for_status()
            scores = {item["id"]: item for item in response.json()["results"]}
        except (httpx.HTTPError, KeyError, TypeError, ValueError):
            logger.warning("Triage service unavailable; returning unscored messages", exc_info=True)
            return emails
        return [
            email.model_copy(
                update={
                    "priority": scores[email.id]["priority"],
                    "priority_score": scores[email.id]["score"],
                    "priority_signals": scores[email.id].get("signals", []),
                }
            )
            if email.id in scores
            else email
            for email in emails
        ]
