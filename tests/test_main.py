"""
Basic integration tests. Run against a test database — in CI, docker-compose
spins up a real Postgres + Redis service, so these hit real (ephemeral) infra
rather than mocks, which is more representative of how the API actually behaves.
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

TEST_EMAIL = "pytest_user@example.com"
TEST_PASSWORD = "supersecret123"


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_and_login_flow():
    # Register (ignore failure if user already exists from a previous run)
    client.post("/auth/register", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})

    # Login
    response = client.post(
        "/auth/login",
        data={"username": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def _get_auth_headers():
    client.post("/auth/register", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
    response = client.post(
        "/auth/login",
        data={"username": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_and_list_tasks():
    headers = _get_auth_headers()

    create_response = client.post(
        "/tasks/",
        json={"title": "Write scaffold", "description": "Test task", "status": "pending"},
        headers=headers,
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    list_response = client.get("/tasks/", headers=headers)
    assert list_response.status_code == 200
    assert any(t["id"] == task_id for t in list_response.json())


def test_update_and_delete_task():
    headers = _get_auth_headers()

    create_response = client.post(
        "/tasks/",
        json={"title": "Temp task", "status": "pending"},
        headers=headers,
    )
    task_id = create_response.json()["id"]

    update_response = client.patch(
        f"/tasks/{task_id}", json={"status": "done"}, headers=headers
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "done"

    delete_response = client.delete(f"/tasks/{task_id}", headers=headers)
    assert delete_response.status_code == 204
