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


def make_test_conn(schema=SCHEMA):
    """In-memory SQLite connection for unit tests that need a DB but not the full app."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(schema)
    return conn
