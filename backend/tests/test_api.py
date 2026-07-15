from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_reports_service_state() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["version"] == "1.0.0"


def test_status_is_disconnected_without_session() -> None:
    response = client.get("/auth/status")
    assert response.status_code == 200
    assert response.json() == {"connected": False, "email": None, "demo_available": True}


def test_email_routes_require_connection() -> None:
    response = client.get("/emails")
    assert response.status_code == 401
    assert response.json()["detail"] == "Connect Gmail to continue"


def test_knowledge_routes_require_connection() -> None:
    response = client.get("/knowledge")
    assert response.status_code == 401
    assert response.json()["detail"] == "Connect Gmail to continue"


def test_rejects_oversized_page() -> None:
    response = client.get("/emails?max_results=500")
    assert response.status_code == 422
