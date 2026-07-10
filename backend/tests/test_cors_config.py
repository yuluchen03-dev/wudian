from fastapi.testclient import TestClient

from app.main import app


def test_dev_frontend_port_3001_is_allowed_for_cors_preflight():
    client = TestClient(app)

    response = client.options(
        "/api/classics/books",
        headers={
            "Origin": "http://localhost:3001",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3001"
