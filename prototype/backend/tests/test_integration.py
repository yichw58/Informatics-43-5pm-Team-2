"""
Integration tests — exercise full HTTP request/response cycles against a real
(temp-file) SQLite database via FastAPI's TestClient.
"""
import sqlite3

import pytest


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def test_register_returns_token_and_user(client):
    resp = client.post("/api/auth/register", json={
        "email": "new@example.com",
        "displayName": "New User",
        "password": "strongpass",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["user"]["displayName"] == "New User"
    assert data["user"]["email"] == "new@example.com"
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]


def test_duplicate_email_rejected(client, user_a):
    resp = client.post("/api/auth/register", json={
        "email": "alice@test.com",
        "displayName": "Alice2",
        "password": "anotherpass",
    })
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()


def test_login_valid_credentials(client, user_a):
    resp = client.post("/api/auth/login", json={
        "email": "alice@test.com",
        "password": "password123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["user"]["email"] == "alice@test.com"


def test_login_wrong_password(client, user_a):
    resp = client.post("/api/auth/login", json={
        "email": "alice@test.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


def test_login_unknown_email(client):
    resp = client.post("/api/auth/login", json={
        "email": "nobody@example.com",
        "password": "whatever",
    })
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Auth protection
# ---------------------------------------------------------------------------

def test_protected_endpoint_requires_token(client):
    """GET /api/map/users without a token should return 401."""
    resp = client.get("/api/map/users")
    assert resp.status_code == 401


def test_protected_endpoint_with_invalid_token(client):
    resp = client.get("/api/map/users",
                      headers={"Authorization": "Bearer not.a.real.token"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

def test_get_own_profile(client, user_a):
    resp = client.get("/api/users/me", headers=user_a["headers"])
    assert resp.status_code == 200
    assert resp.json()["displayName"] == "Alice"


def test_update_bio(client, user_a):
    resp = client.patch("/api/users/me",
                        json={"bio": "Love hiking and coffee."},
                        headers=user_a["headers"])
    assert resp.status_code == 200
    assert resp.json()["bio"] == "Love hiking and coffee."


def test_update_display_name(client, user_a):
    resp = client.patch("/api/users/me",
                        json={"displayName": "Alice Updated"},
                        headers=user_a["headers"])
    assert resp.status_code == 200
    assert resp.json()["displayName"] == "Alice Updated"


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------

def test_get_tags_returns_seeded_list(client, user_a):
    resp = client.get("/api/tags", headers=user_a["headers"])
    assert resp.status_code == 200
    tag_ids = [t["id"] for t in resp.json()["tags"]]
    assert "basketball" in tag_ids
    assert "hiking" in tag_ids


def test_subscribe_and_see_tag_on_profile(client, user_a):
    client.post("/api/users/me/tags",
                json={"tagId": "hiking"},
                headers=user_a["headers"])
    resp = client.get("/api/users/me", headers=user_a["headers"])
    assert "hiking" in resp.json()["tags"]


def test_tag_limit_enforced(client, user_a):
    """Subscribing an 11th tag should return 400."""
    all_tags = ["basketball", "tennis", "hiking", "yoga", "biking",
                "surfing", "coffee", "chess", "gaming", "music"]
    for tag in all_tags:
        client.post("/api/users/me/tags", json={"tagId": tag},
                    headers=user_a["headers"])
    # Try to subscribe to an 11th
    resp = client.post("/api/users/me/tags",
                       json={"tagId": "photography"},
                       headers=user_a["headers"])
    assert resp.status_code == 400
    assert "max" in resp.json()["detail"].lower()


def test_unsubscribe_tag(client, user_a):
    client.post("/api/users/me/tags", json={"tagId": "chess"},
                headers=user_a["headers"])
    resp = client.delete("/api/users/me/tags/chess", headers=user_a["headers"])
    assert resp.status_code == 200
    assert "chess" not in resp.json()["tags"]


# ---------------------------------------------------------------------------
# Map
# ---------------------------------------------------------------------------

def test_map_excludes_self(client, user_a):
    """A user should not see themselves on the map."""
    # Make user_a visible
    client.patch("/api/users/me/location",
                 json={"lat": 33.6405, "lng": -117.8443, "visible": True},
                 headers=user_a["headers"])
    resp = client.get("/api/map/users", headers=user_a["headers"])
    assert resp.status_code == 200
    ids = [u["id"] for u in resp.json()["users"]]
    assert user_a["user"]["id"] not in ids


def test_map_filter_by_tag(client, user_a, user_b, temp_db):
    """Only users with the filtered tag should appear."""
    # Make both visible at the same coords
    for u in (user_a, user_b):
        client.patch("/api/users/me/location",
                     json={"lat": 33.6405, "lng": -117.8443, "visible": True},
                     headers=u["headers"])
    # Give only user_b the hiking tag
    client.post("/api/users/me/tags", json={"tagId": "hiking"},
                headers=user_b["headers"])

    resp = client.get("/api/map/users?tags=hiking", headers=user_a["headers"])
    assert resp.status_code == 200
    users = resp.json()["users"]
    ids = [u["id"] for u in users]
    assert user_b["user"]["id"] in ids
    assert user_a["user"]["id"] not in ids


def test_map_filter_by_status(client, user_a, user_b):
    """Status filter should only return users with matching status."""
    for u in (user_a, user_b):
        client.patch("/api/users/me/location",
                     json={"lat": 33.6405, "lng": -117.8443, "visible": True},
                     headers=u["headers"])
    client.patch(f"/api/users/{user_b['user']['id']}/status",
                 json={"status": "open"},
                 headers=user_b["headers"])

    resp = client.get("/api/map/users?status=open", headers=user_a["headers"])
    ids = [u["id"] for u in resp.json()["users"]]
    assert user_b["user"]["id"] in ids
    # user_a is busy (default) and also excluded from self
    assert user_a["user"]["id"] not in ids


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

def test_status_update_own(client, user_a):
    uid = user_a["user"]["id"]
    resp = client.patch(f"/api/users/{uid}/status",
                        json={"status": "open"},
                        headers=user_a["headers"])
    assert resp.status_code == 200
    assert resp.json()["status"] == "open"


def test_status_update_other_user_forbidden(client, user_a, user_b):
    uid = user_b["user"]["id"]
    resp = client.patch(f"/api/users/{uid}/status",
                        json={"status": "open"},
                        headers=user_a["headers"])
    assert resp.status_code == 403


def test_invalid_status_value(client, user_a):
    uid = user_a["user"]["id"]
    resp = client.patch(f"/api/users/{uid}/status",
                        json={"status": "maybe"},
                        headers=user_a["headers"])
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Connection requests
# ---------------------------------------------------------------------------

def test_connection_request_out_of_range(client, user_a, user_b, temp_db):
    """Request to a user >0.5 miles away should be rejected."""
    # Move user_b to New York directly in the DB
    db = sqlite3.connect(temp_db)
    db.execute("UPDATE users SET lat = 40.7128, lng = -74.0060 WHERE id = ?",
               (user_b["user"]["id"],))
    db.commit()
    db.close()

    resp = client.post("/api/connections/request",
                       json={"toUserId": user_b["user"]["id"], "introMessage": "Hi!"},
                       headers=user_a["headers"])
    assert resp.status_code == 400
    assert "range" in resp.json()["detail"].lower()


def test_connection_request_to_self_rejected(client, user_a):
    resp = client.post("/api/connections/request",
                       json={"toUserId": user_a["user"]["id"], "introMessage": ""},
                       headers=user_a["headers"])
    assert resp.status_code == 400


def test_connection_request_in_range(client, user_a, user_b):
    """Two users at the same coordinates can connect."""
    resp = client.post("/api/connections/request",
                       json={"toUserId": user_b["user"]["id"],
                             "introMessage": "Want to hike?"},
                       headers=user_a["headers"])
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"


def test_duplicate_pending_request_rejected(client, user_a, user_b):
    """Sending a second request while one is pending should return 400."""
    client.post("/api/connections/request",
                json={"toUserId": user_b["user"]["id"], "introMessage": ""},
                headers=user_a["headers"])
    resp = client.post("/api/connections/request",
                       json={"toUserId": user_b["user"]["id"], "introMessage": "Again"},
                       headers=user_a["headers"])
    assert resp.status_code == 400
    assert "pending" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Privacy — blackout zones
# ---------------------------------------------------------------------------

def test_add_and_list_blackout_zone(client, user_a):
    resp = client.post("/api/privacy/blackout",
                       json={"label": "Home", "centerLat": 33.64,
                             "centerLng": -117.84, "radiusMiles": 0.2},
                       headers=user_a["headers"])
    assert resp.status_code == 200
    zone_id = resp.json()["id"]

    list_resp = client.get("/api/privacy/blackout", headers=user_a["headers"])
    assert list_resp.status_code == 200
    ids = [z["id"] for z in list_resp.json()["zones"]]
    assert zone_id in ids


def test_delete_blackout_zone(client, user_a):
    add_resp = client.post("/api/privacy/blackout",
                           json={"label": "Work", "centerLat": 33.64,
                                 "centerLng": -117.84, "radiusMiles": 0.1},
                           headers=user_a["headers"])
    zone_id = add_resp.json()["id"]
    del_resp = client.delete(f"/api/privacy/blackout/{zone_id}",
                             headers=user_a["headers"])
    assert del_resp.status_code == 200

    list_resp = client.get("/api/privacy/blackout", headers=user_a["headers"])
    ids = [z["id"] for z in list_resp.json()["zones"]]
    assert zone_id not in ids


# ---------------------------------------------------------------------------
# Location privacy — schedule
# ---------------------------------------------------------------------------

def test_put_and_get_schedule(client, user_a):
    resp = client.put("/api/privacy/schedule",
                      json={"shareFrom": "09:00", "shareUntil": "21:00", "enabled": True},
                      headers=user_a["headers"])
    assert resp.status_code == 200

    get_resp = client.get("/api/privacy/schedule", headers=user_a["headers"])
    data = get_resp.json()
    assert data["shareFrom"] == "09:00"
    assert data["shareUntil"] == "21:00"
    assert data["enabled"] is True


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------

def test_leaderboard_returns_list(client, user_a):
    resp = client.get("/api/leaderboard", headers=user_a["headers"])
    assert resp.status_code == 200
    assert "leaderboard" in resp.json()
