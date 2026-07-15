import httpx

from app.config import Settings
from app.models import EmailSummary
from app.triage import TriageClient


def sample_email() -> EmailSummary:
    return EmailSummary(
        id="m-1",
        thread_id="t-1",
        subject="Approval needed",
        sender="client@example.com",
        date="2026-07-13T12:00:00Z",
        snippet="Please confirm today",
        is_unread=True,
    )


def test_triage_client_enriches_messages(monkeypatch) -> None:
    def fake_post(*args, **kwargs) -> httpx.Response:  # noqa: ANN002, ANN003
        request = httpx.Request("POST", str(args[0]))
        return httpx.Response(
            200,
            request=request,
            json={
                "results": [
                    {
                        "id": "m-1",
                        "score": 75,
                        "priority": "urgent",
                        "signals": ["Deadline detected"],
                    }
                ]
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    client = TriageClient(Settings(triage_service_url="http://triage:8080"))

    enriched = client.enrich([sample_email()])

    assert enriched[0].priority == "urgent"
    assert enriched[0].priority_score == 75
    assert enriched[0].priority_signals == ["Deadline detected"]


def test_triage_client_fails_open_when_service_is_unavailable(monkeypatch) -> None:
    def failing_post(*args, **kwargs) -> httpx.Response:  # noqa: ANN002, ANN003
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx, "post", failing_post)
    client = TriageClient(Settings(triage_service_url="http://triage:8080"))
    original = sample_email()

    assert client.enrich([original]) == [original]
