import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402


def auth(client, email):
    client.post("/v1/auth/register", json={"email": email, "password": "password123"})
    token = client.post("/v1/auth/login",
                        json={"email": email, "password": "password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_full_flow():
    with TestClient(app) as c:
        h = auth(c, "a@example.com")

        r = c.post("/v1/tasks", headers=h, json={
            "title": "Finish SIS 1", "priority": "high", "due_date": "2026-10-20T18:00:00Z"})
        assert r.status_code == 201
        tid = r.json()["id"]

        assert c.get(f"/v1/tasks/{tid}", headers=h).json()["title"] == "Finish SIS 1"

        r = c.patch(f"/v1/tasks/{tid}", headers=h, json={"status": "done"})
        assert r.json()["status"] == "done"

        lst = c.get("/v1/tasks?status=done", headers=h).json()
        assert lst["total"] == 1

        assert c.delete(f"/v1/tasks/{tid}", headers=h).status_code == 204
        assert c.get(f"/v1/tasks/{tid}", headers=h).status_code == 404


def test_errors_and_isolation():
    with TestClient(app) as c:
        a, b = auth(c, "u1@example.com"), auth(c, "u2@example.com")
        assert c.get("/v1/tasks").status_code == 401                       # no token
        assert c.post("/v1/tasks", headers=a, json={"title": ""}).status_code == 400  # bad input
        tid = c.post("/v1/tasks", headers=a, json={"title": "private"}).json()["id"]
        assert c.get(f"/v1/tasks/{tid}", headers=b).status_code == 404     # other user's task
        assert c.get("/v1/tasks", headers=b).json()["total"] == 0


def test_idempotency_key():
    with TestClient(app) as c:
        h = {**auth(c, "i@example.com"), "Idempotency-Key": "abc-123"}
        r1 = c.post("/v1/tasks", headers=h, json={"title": "once"})
        r2 = c.post("/v1/tasks", headers=h, json={"title": "once"})
        assert r1.status_code == 201 and r2.status_code == 200
        assert r1.json()["id"] == r2.json()["id"]
        assert c.get("/v1/tasks", headers=h).json()["total"] == 1
