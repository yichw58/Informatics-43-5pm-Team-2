import sqlite3
import pytest
import database
from fastapi.testclient import TestClient
from database import init_db, SCHEMA


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Each test gets its own isolated SQLite file; DB_PATH is patched globally."""
    db_file = str(tmp_path / "test_mingle.db")
    monkeypatch.setattr(database, "DB_PATH", db_file)
    init_db()
    yield db_file


@pytest.fixture
def client(temp_db):
    from main import app
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture
def user_a(client):
    resp = client.post("/api/auth/register", json={
        "email": "alice@test.com",
        "displayName": "Alice",
        "password": "password123",
    })
    assert resp.status_code == 200
    data = resp.json()
    return {"token": data["token"], "user": data["user"],
            "headers": {"Authorization": f"Bearer {data['token']}"}}


@pytest.fixture
def user_b(client):
    resp = client.post("/api/auth/register", json={
        "email": "bob@test.com",
        "displayName": "Bob",
        "password": "password456",
    })
    assert resp.status_code == 200
    data = resp.json()
    return {"token": data["token"], "user": data["user"],
            "headers": {"Authorization": f"Bearer {data['token']}"}}


@pytest.fixture
def user_c(client):
    resp = client.post("/api/auth/register", json={
        "email": "carol@test.com",
        "displayName": "Carol",
        "password": "password789",
    })
    assert resp.status_code == 200
    data = resp.json()
    return {"token": data["token"], "user": data["user"],
            "headers": {"Authorization": f"Bearer {data['token']}"}}


@pytest.fixture
def connected_pair(client, user_a, user_b):
    """user_a sends a connection request and user_b accepts it.
    Returns both users plus the resulting thread_id."""
    req = client.post("/api/connections/request",
                      json={"toUserId": user_b["user"]["id"], "introMessage": "Hey!"},
                      headers=user_a["headers"])
    assert req.status_code == 200
    request_id = req.json()["id"]

    accept = client.patch(f"/api/connections/requests/{request_id}",
                          json={"accepted": True},
                          headers=user_b["headers"])
    assert accept.status_code == 200
    thread_id = accept.json()["threadId"]

    return {
        "user_a": user_a,
        "user_b": user_b,
        "thread_id": thread_id,
        "request_id": request_id,
    }


def make_test_conn(schema=SCHEMA):
    """In-memory SQLite connection for unit tests that need a DB but not the full app."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(schema)
    return conn
