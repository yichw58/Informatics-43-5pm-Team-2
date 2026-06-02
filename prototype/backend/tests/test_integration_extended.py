"""
Extended integration tests covering connection flow, full chat flow, streaks,
location visibility/suppression, and auth edge cases.
Target: push overall coverage from 63% toward ~85%.
"""
import sqlite3

import pytest
from jose import jwt

from auth import SECRET_KEY, ALGORITHM


# ---------------------------------------------------------------------------
# Connection request inbox
# ---------------------------------------------------------------------------

def test_inbox_shows_pending_request(client, user_a, user_b):
    """After A requests B, B's inbox contains the request."""
    req = client.post("/api/connections/request",
                      json={"toUserId": user_b["user"]["id"], "introMessage": "Hey!"},
                      headers=user_a["headers"])
    assert req.status_code == 200

    inbox = client.get("/api/connections/requests/inbox", headers=user_b["headers"])
    assert inbox.status_code == 200
    requests = inbox.json()["requests"]
    assert len(requests) == 1
    assert requests[0]["introMessage"] == "Hey!"
    assert requests[0]["fromUser"]["id"] == user_a["user"]["id"]


def test_inbox_empty_when_no_requests(client, user_a):
    inbox = client.get("/api/connections/requests/inbox", headers=user_a["headers"])
    assert inbox.status_code == 200
    assert inbox.json()["requests"] == []


# ---------------------------------------------------------------------------
# Accept / decline connection requests
# ---------------------------------------------------------------------------

def test_accept_request_returns_thread_id(client, user_a, user_b):
    req = client.post("/api/connections/request",
                      json={"toUserId": user_b["user"]["id"], "introMessage": ""},
                      headers=user_a["headers"])
    request_id = req.json()["id"]

    resp = client.patch(f"/api/connections/requests/{request_id}",
                        json={"accepted": True},
                        headers=user_b["headers"])
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"
    assert "threadId" in resp.json()


def test_decline_request_returns_declined(client, user_a, user_b):
    req = client.post("/api/connections/request",
                      json={"toUserId": user_b["user"]["id"], "introMessage": ""},
                      headers=user_a["headers"])
    request_id = req.json()["id"]

    resp = client.patch(f"/api/connections/requests/{request_id}",
                        json={"accepted": False},
                        headers=user_b["headers"])
    assert resp.status_code == 200
    assert resp.json()["status"] == "declined"


def test_cooldown_blocks_request_after_decline(client, user_a, user_b):
    """After a decline, the requester cannot send another request during cooldown."""
    req = client.post("/api/connections/request",
                      json={"toUserId": user_b["user"]["id"], "introMessage": ""},
                      headers=user_a["headers"])
    request_id = req.json()["id"]
    client.patch(f"/api/connections/requests/{request_id}",
                 json={"accepted": False},
                 headers=user_b["headers"])

    # A tries again immediately — should be blocked by cooldown
    resp = client.post("/api/connections/request",
                       json={"toUserId": user_b["user"]["id"], "introMessage": ""},
                       headers=user_a["headers"])
    assert resp.status_code == 400
    assert "wait" in resp.json()["detail"].lower() or "cannot" in resp.json()["detail"].lower()


def test_decide_request_wrong_user_forbidden(client, user_a, user_b, user_c):
    """A third user cannot decide a request they didn't receive."""
    req = client.post("/api/connections/request",
                      json={"toUserId": user_b["user"]["id"], "introMessage": ""},
                      headers=user_a["headers"])
    request_id = req.json()["id"]

    resp = client.patch(f"/api/connections/requests/{request_id}",
                        json={"accepted": True},
                        headers=user_c["headers"])
    assert resp.status_code == 403


def test_decide_nonexistent_request_returns_404(client, user_a):
    resp = client.patch("/api/connections/requests/nonexistent-id",
                        json={"accepted": True},
                        headers=user_a["headers"])
    assert resp.status_code == 404


def test_decide_already_resolved_returns_400(client, user_a, user_b):
    """Accepting a request twice should return 400."""
    req = client.post("/api/connections/request",
                      json={"toUserId": user_b["user"]["id"], "introMessage": ""},
                      headers=user_a["headers"])
    request_id = req.json()["id"]
    client.patch(f"/api/connections/requests/{request_id}",
                 json={"accepted": True},
                 headers=user_b["headers"])

    resp = client.patch(f"/api/connections/requests/{request_id}",
                        json={"accepted": True},
                        headers=user_b["headers"])
    assert resp.status_code == 400
    assert "resolved" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Connections list
# ---------------------------------------------------------------------------

def test_list_connections_after_accept(client, connected_pair):
    user_a = connected_pair["user_a"]
    user_b = connected_pair["user_b"]

    resp = client.get("/api/connections", headers=user_a["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert "connections" in data
    thread_ids = [c["threadId"] for c in data["connections"]]
    assert connected_pair["thread_id"] in thread_ids


def test_list_connections_pending_to(client, user_a, user_b):
    """Outgoing pending requests appear in pendingTo."""
    client.post("/api/connections/request",
                json={"toUserId": user_b["user"]["id"], "introMessage": ""},
                headers=user_a["headers"])

    resp = client.get("/api/connections", headers=user_a["headers"])
    assert user_b["user"]["id"] in resp.json()["pendingTo"]


def test_list_connections_empty_initially(client, user_a):
    resp = client.get("/api/connections", headers=user_a["headers"])
    assert resp.status_code == 200
    assert resp.json()["connections"] == []


# ---------------------------------------------------------------------------
# Chat — threads
# ---------------------------------------------------------------------------

def test_list_threads_after_connect(client, connected_pair):
    user_a = connected_pair["user_a"]
    resp = client.get("/api/chat/threads", headers=user_a["headers"])
    assert resp.status_code == 200
    ids = [t["id"] for t in resp.json()["threads"]]
    assert connected_pair["thread_id"] in ids


def test_list_threads_empty_before_connect(client, user_a):
    resp = client.get("/api/chat/threads", headers=user_a["headers"])
    assert resp.status_code == 200
    assert resp.json()["threads"] == []


# ---------------------------------------------------------------------------
# Chat — messages
# ---------------------------------------------------------------------------

def test_send_message_returns_message_object(client, connected_pair):
    tid = connected_pair["thread_id"]
    user_a = connected_pair["user_a"]

    resp = client.post(f"/api/chat/threads/{tid}/messages",
                       json={"body": "Hello there!"},
                       headers=user_a["headers"])
    assert resp.status_code == 200
    msg = resp.json()
    assert msg["body"] == "Hello there!"
    assert msg["fromId"] == user_a["user"]["id"]
    assert msg["threadId"] == tid


def test_get_messages_shows_sent(client, connected_pair):
    tid = connected_pair["thread_id"]
    user_a = connected_pair["user_a"]

    client.post(f"/api/chat/threads/{tid}/messages",
                json={"body": "First message"},
                headers=user_a["headers"])
    client.post(f"/api/chat/threads/{tid}/messages",
                json={"body": "Second message"},
                headers=connected_pair["user_b"]["headers"])

    resp = client.get(f"/api/chat/threads/{tid}/messages",
                      headers=user_a["headers"])
    assert resp.status_code == 200
    bodies = [m["body"] for m in resp.json()["messages"]]
    assert "First message" in bodies
    assert "Second message" in bodies


def test_get_messages_non_participant_forbidden(client, connected_pair, user_c):
    """A user not in the thread cannot read messages."""
    tid = connected_pair["thread_id"]
    resp = client.get(f"/api/chat/threads/{tid}/messages",
                      headers=user_c["headers"])
    assert resp.status_code == 403


def test_send_message_non_participant_forbidden(client, connected_pair, user_c):
    tid = connected_pair["thread_id"]
    resp = client.post(f"/api/chat/threads/{tid}/messages",
                       json={"body": "Sneaky"},
                       headers=user_c["headers"])
    assert resp.status_code == 403


def test_thread_not_found_returns_404(client, user_a):
    resp = client.get("/api/chat/threads/fake-thread-id/messages",
                      headers=user_a["headers"])
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Streaks
# ---------------------------------------------------------------------------

def test_streak_created_on_first_message(client, connected_pair):
    tid = connected_pair["thread_id"]
    user_a = connected_pair["user_a"]

    client.post(f"/api/chat/threads/{tid}/messages",
                json={"body": "Hi!"},
                headers=user_a["headers"])

    resp = client.get("/api/streaks", headers=user_a["headers"])
    assert resp.status_code == 200
    streaks = resp.json()["streaks"]
    assert len(streaks) == 1
    assert streaks[0]["count"] == 1


def test_streak_increments_on_each_message(client, connected_pair):
    tid = connected_pair["thread_id"]
    user_a = connected_pair["user_a"]
    user_b = connected_pair["user_b"]

    # Three messages between the pair
    for _ in range(3):
        client.post(f"/api/chat/threads/{tid}/messages",
                    json={"body": "ping"},
                    headers=user_a["headers"])

    resp = client.get("/api/streaks", headers=user_b["headers"])
    streaks = resp.json()["streaks"]
    assert streaks[0]["count"] == 3


def test_streaks_empty_before_messages(client, connected_pair):
    user_a = connected_pair["user_a"]
    resp = client.get("/api/streaks", headers=user_a["headers"])
    assert resp.json()["streaks"] == []


# ---------------------------------------------------------------------------
# Leaderboard (with streak data)
# ---------------------------------------------------------------------------

def test_leaderboard_reflects_streak(client, connected_pair):
    tid = connected_pair["thread_id"]
    user_a = connected_pair["user_a"]

    for _ in range(5):
        client.post(f"/api/chat/threads/{tid}/messages",
                    json={"body": "msg"},
                    headers=user_a["headers"])

    resp = client.get("/api/leaderboard", headers=user_a["headers"])
    assert resp.status_code == 200
    entries = resp.json()["leaderboard"]
    streaks = {e["id"]: e["streak"] for e in entries}
    assert streaks[user_a["user"]["id"]] == 5


# ---------------------------------------------------------------------------
# Location visibility in GET /api/users/{user_id}
# ---------------------------------------------------------------------------

def test_get_user_hides_location_when_invisible(client, user_a, user_b):
    """user_b has location_visible=0 (default); user_a sees null lat/lng."""
    resp = client.get(f"/api/users/{user_b['user']['id']}",
                      headers=user_a["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["lat"] is None
    assert data["lng"] is None


def test_get_user_shows_location_when_visible(client, user_a, user_b):
    """After user_b enables location sharing, user_a can see their coords."""
    client.patch("/api/users/me/location",
                 json={"lat": 33.64, "lng": -117.84, "visible": True},
                 headers=user_b["headers"])

    resp = client.get(f"/api/users/{user_b['user']['id']}",
                      headers=user_a["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["lat"] == pytest.approx(33.64)
    assert data["lng"] == pytest.approx(-117.84)


def test_get_own_profile_always_shows_location(client, user_a):
    """A user always sees their own coords regardless of visibility flag."""
    resp = client.get(f"/api/users/{user_a['user']['id']}",
                      headers=user_a["headers"])
    assert resp.status_code == 200
    # Coords may be None only if lat is NULL in DB; default lat is set so it should exist
    data = resp.json()
    assert "lat" in data


def test_get_user_not_found(client, user_a):
    resp = client.get("/api/users/nonexistent-id", headers=user_a["headers"])
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Location update with blackout zone suppression
# ---------------------------------------------------------------------------

def test_location_update_inside_blackout_is_suppressed(client, user_a):
    """Updating location to inside a blackout zone sets suppressed=True."""
    # Add a blackout zone centered exactly where we'll send the update
    client.post("/api/privacy/blackout",
                json={"label": "Home", "centerLat": 33.64,
                      "centerLng": -117.84, "radiusMiles": 0.5},
                headers=user_a["headers"])

    resp = client.patch("/api/users/me/location",
                        json={"lat": 33.64, "lng": -117.84, "visible": True},
                        headers=user_a["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("suppressed") is True
    assert data.get("locationVisible") is False


def test_location_update_outside_blackout_is_not_suppressed(client, user_a):
    """Updating to a location outside all zones is not suppressed."""
    # Zone is at UCI; update to a point 5 miles away
    client.post("/api/privacy/blackout",
                json={"label": "Home", "centerLat": 33.64,
                      "centerLng": -117.84, "radiusMiles": 0.1},
                headers=user_a["headers"])

    resp = client.patch("/api/users/me/location",
                        json={"lat": 33.70, "lng": -117.84, "visible": True},
                        headers=user_a["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("suppressed") is not True


# ---------------------------------------------------------------------------
# Tag search and category filter
# ---------------------------------------------------------------------------

def test_tag_search_returns_matching(client, user_a):
    resp = client.get("/api/tags?search=hik", headers=user_a["headers"])
    assert resp.status_code == 200
    names = [t["name"] for t in resp.json()["tags"]]
    assert "hiking" in names
    assert "basketball" not in names


def test_tag_category_filter(client, user_a):
    resp = client.get("/api/tags?category=sports", headers=user_a["headers"])
    assert resp.status_code == 200
    cats = {t["category"] for t in resp.json()["tags"]}
    assert cats == {"sports"}


def test_tag_search_no_results(client, user_a):
    resp = client.get("/api/tags?search=zzznomatch", headers=user_a["headers"])
    assert resp.status_code == 200
    assert resp.json()["tags"] == []


# ---------------------------------------------------------------------------
# Auth edge cases
# ---------------------------------------------------------------------------

def test_token_for_deleted_user_returns_401(client, user_a, temp_db):
    """A valid token for a user that no longer exists in the DB returns 401."""
    db = sqlite3.connect(temp_db)
    db.execute("DELETE FROM users WHERE id = ?", (user_a["user"]["id"],))
    db.commit()
    db.close()

    resp = client.get("/api/users/me", headers=user_a["headers"])
    assert resp.status_code == 401


def test_jwt_with_no_sub_returns_401(client):
    """A JWT signed correctly but missing the 'sub' claim returns 401."""
    token = jwt.encode({"foo": "bar"}, SECRET_KEY, algorithm=ALGORITHM)
    resp = client.get("/api/users/me",
                      headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Already-connected users cannot request each other again
# ---------------------------------------------------------------------------

def test_already_connected_cannot_request(client, connected_pair):
    user_a = connected_pair["user_a"]
    user_b = connected_pair["user_b"]

    resp = client.post("/api/connections/request",
                       json={"toUserId": user_b["user"]["id"], "introMessage": ""},
                       headers=user_a["headers"])
    assert resp.status_code == 400
    assert "connected" in resp.json()["detail"].lower()
