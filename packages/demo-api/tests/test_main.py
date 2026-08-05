from demo_api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_returns_success() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"success": True}


def test_index_links_to_docs() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert 'href="/docs"' in response.text


def test_docs_are_served() -> None:
    response = client.get("/docs")
    assert response.status_code == 200
