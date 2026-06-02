import json
import math
import os
import uuid
from datetime import datetime, timedelta, timezone

import aiofiles
from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from auth import (
    create_token,
    decode_token,
    get_current_user,
    hash_password,
    verify_password,
)
from database import get_db, init_db
from models import (
    BlackoutZoneBody,
    ConnectionDecision,
    ConnectionRequestBody,
    LocationUpdate,
    LoginRequest,
    MessageBody,
    ProfileUpdate,
    RegisterRequest,
    ScheduleBody,
    StatusUpdate,
    TagAction,
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
PHOTOS_DIR = os.path.join(STATIC_DIR, "photos")
MAX_TAGS = 10
PROXIMITY_LIMIT_MILES = 0.5
COOLDOWN_HOURS = 24
MAX_PHOTO_BYTES = 5 * 1024 * 1024

app = FastAPI(title="Mingle API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    os.makedirs(PHOTOS_DIR, exist_ok=True)
    init_db()


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ---------------------------------------------------------------------------
# WebSocket connection manager
# ---------------------------------------------------------------------------

connected_clients: dict[str, WebSocket] = {}


async def push(user_id: str, event: dict):
    ws = connected_clients.get(user_id)
    if ws is None:
        return
    try:
        await ws.send_text(json.dumps(event))
    except Exception:
        connected_clients.pop(user_id, None)


async def broadcast(event: dict, exclude: str | None = None):
    for cid, ws in list(connected_clients.items()):
        if cid == exclude:
            continue
        try:
            await ws.send_text(json.dumps(event))
        except Exception:
            connected_clients.pop(cid, None)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def haversine_miles(lat1, lng1, lat2, lng2) -> float:
    r = 3958.8  # Earth radius in miles
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def get_user_tags(conn, user_id: str) -> list[str]:
    rows = conn.execute(
        "SELECT tag_id FROM user_tags WHERE user_id = ?", (user_id,)
    ).fetchall()
    return [r["tag_id"] for r in rows]


def serialize_user(conn, row, include_private=False) -> dict:
    user = {
        "id": row["id"],
        "displayName": row["display_name"],
        "bio": row["bio"] or "",
        "photoUrl": row["photo_url"],
        "tags": get_user_tags(conn, row["id"]),
        "status": row["status"],
        "lat": row["lat"],
        "lng": row["lng"],
        "locationVisible": bool(row["location_visible"]),
    }
    if include_private:
        user["email"] = row["email"]
    return user


def fetch_user_row(conn, user_id: str):
    return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def pair(a: str, b: str) -> tuple[str, str]:
    """Order a user pair deterministically so streak/thread lookups are symmetric."""
    return (a, b) if a <= b else (b, a)


def is_location_suppressed(conn, user_id: str, lat, lng) -> bool:
    """Return True if the user's location should be hidden right now, based on
    their schedule window and/or any blackout zone they have configured."""
    if lat is None or lng is None:
        return False

    schedule = conn.execute(
        "SELECT share_from, share_until, enabled FROM location_schedules WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if schedule is not None and schedule["enabled"]:
        now = now_utc().strftime("%H:%M")
        share_from = schedule["share_from"]
        share_until = schedule["share_until"]
        if share_from <= share_until:
            # Same-day window, e.g. 08:00..22:00.
            if not (share_from <= now <= share_until):
                return True
        else:
            # Overnight window, e.g. 22:00..06:00.
            if share_until < now < share_from:
                return True

    zones = conn.execute(
        "SELECT center_lat, center_lng, radius_miles FROM blackout_zones WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    for z in zones:
        dist = haversine_miles(lat, lng, z["center_lat"], z["center_lng"])
        if dist <= z["radius_miles"]:
            return True

    return False


def has_privacy_rules(conn, user_id: str) -> bool:
    """True if the user has an enabled schedule or any blackout zone, so callers
    can skip the suppression check entirely and avoid needless per-user queries."""
    sched = conn.execute(
        "SELECT 1 FROM location_schedules WHERE user_id = ? AND enabled = 1",
        (user_id,),
    ).fetchone()
    if sched is not None:
        return True
    zone = conn.execute(
        "SELECT 1 FROM blackout_zones WHERE user_id = ? LIMIT 1", (user_id,)
    ).fetchone()
    return zone is not None


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@app.post("/api/auth/register")
def register(body: RegisterRequest):
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE email = ?", (body.email,)
        ).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        user_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO users (id, email, display_name, password_hash) VALUES (?, ?, ?, ?)",
            (user_id, body.email, body.displayName, hash_password(body.password)),
        )
        conn.commit()
        row = fetch_user_row(conn, user_id)
        return {"token": create_token(user_id), "user": serialize_user(conn, row, include_private=True)}
    finally:
        conn.close()


@app.post("/api/auth/login")
def login(body: LoginRequest):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (body.email,)
        ).fetchone()
        if row is None or not verify_password(body.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        return {"token": create_token(row["id"]), "user": serialize_user(conn, row, include_private=True)}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Users / Profile
# ---------------------------------------------------------------------------

@app.get("/api/users/me")
def get_me(current=Depends(get_current_user)):
    conn = get_db()
    try:
        row = fetch_user_row(conn, current["id"])
        return serialize_user(conn, row, include_private=True)
    finally:
        conn.close()


@app.patch("/api/users/me")
def update_me(body: ProfileUpdate, current=Depends(get_current_user)):
    conn = get_db()
    try:
        if body.displayName is not None:
            conn.execute(
                "UPDATE users SET display_name = ? WHERE id = ?",
                (body.displayName, current["id"]),
            )
        if body.bio is not None:
            conn.execute(
                "UPDATE users SET bio = ? WHERE id = ?", (body.bio, current["id"])
            )
        conn.commit()
        row = fetch_user_row(conn, current["id"])
        return serialize_user(conn, row, include_private=True)
    finally:
        conn.close()


@app.post("/api/users/me/photo")
async def upload_photo(file: UploadFile = File(...), current=Depends(get_current_user)):
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="Unsupported image type")
    data = await file.read()
    if len(data) > MAX_PHOTO_BYTES:
        raise HTTPException(status_code=400, detail="Image too large. Maximum size is 5 MB.")
    os.makedirs(PHOTOS_DIR, exist_ok=True)
    dest = os.path.join(PHOTOS_DIR, f"{current['id']}.jpg")
    async with aiofiles.open(dest, "wb") as f:
        await f.write(data)
    photo_url = f"/static/photos/{current['id']}.jpg"
    conn = get_db()
    try:
        conn.execute(
            "UPDATE users SET photo_url = ? WHERE id = ?", (photo_url, current["id"])
        )
        conn.commit()
    finally:
        conn.close()
    return {"photoUrl": photo_url}


@app.get("/api/users/{user_id}")
def get_user(user_id: str, current=Depends(get_current_user)):
    conn = get_db()
    try:
        row = fetch_user_row(conn, user_id)
        if row is None:
            raise HTTPException(status_code=404, detail="User not found")
        data = serialize_user(conn, row)
        if not data["locationVisible"] and user_id != current["id"]:
            data["lat"] = None
            data["lng"] = None
        return data
    finally:
        conn.close()


@app.patch("/api/users/{user_id}/status")
async def update_status(user_id: str, body: StatusUpdate, current=Depends(get_current_user)):
    if user_id != current["id"]:
        raise HTTPException(status_code=403, detail="Cannot change another user's status")
    if body.status not in ("open", "busy"):
        raise HTTPException(status_code=400, detail="Invalid status")
    conn = get_db()
    try:
        conn.execute("UPDATE users SET status = ? WHERE id = ?", (body.status, user_id))
        conn.commit()
    finally:
        conn.close()
    await broadcast(
        {"event": "status_update", "userId": user_id, "status": body.status},
        exclude=user_id,
    )
    return {"success": True, "status": body.status}


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------

@app.get("/api/tags")
def get_tags(search: str | None = None, category: str | None = None):
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM tags").fetchall()
    finally:
        conn.close()
    tags = [
        {"id": r["id"], "name": r["name"], "emoji": r["emoji"], "category": r["category"]}
        for r in rows
    ]
    if search:
        tags = [t for t in tags if search.lower() in t["name"].lower()]
    if category:
        tags = [t for t in tags if t["category"] == category]
    return {"tags": tags}


@app.post("/api/users/me/tags")
def subscribe_tag(body: TagAction, current=Depends(get_current_user)):
    conn = get_db()
    try:
        tag = conn.execute("SELECT id FROM tags WHERE id = ?", (body.tagId,)).fetchone()
        if tag is None:
            raise HTTPException(status_code=404, detail="Tag not found")
        current_tags = get_user_tags(conn, current["id"])
        if body.tagId not in current_tags and len(current_tags) >= MAX_TAGS:
            raise HTTPException(status_code=400, detail=f"Max {MAX_TAGS} tags reached")
        conn.execute(
            "INSERT OR IGNORE INTO user_tags (user_id, tag_id) VALUES (?, ?)",
            (current["id"], body.tagId),
        )
        conn.commit()
        return {"tags": get_user_tags(conn, current["id"])}
    finally:
        conn.close()


@app.delete("/api/users/me/tags/{tag_id}")
def unsubscribe_tag(tag_id: str, current=Depends(get_current_user)):
    conn = get_db()
    try:
        conn.execute(
            "DELETE FROM user_tags WHERE user_id = ? AND tag_id = ?",
            (current["id"], tag_id),
        )
        conn.commit()
        return {"tags": get_user_tags(conn, current["id"])}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Map
# ---------------------------------------------------------------------------

@app.get("/api/map/users")
def get_map_users(
    tags: str | None = None,
    status: str | None = None,
    current=Depends(get_current_user),
):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM users WHERE location_visible = 1 AND id != ?",
            (current["id"],),
        ).fetchall()
        users = [serialize_user(conn, r) for r in rows]

        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
            if tag_list:
                users = [u for u in users if any(t in u["tags"] for t in tag_list)]
        if status and status != "all":
            users = [u for u in users if u["status"] == status]

        # Drop users whose location is currently suppressed by their own
        # schedule/blackout rules. Skip the check entirely for users with no
        # active rules to avoid an N+1 of suppression queries.
        visible_users = []
        for u in users:
            if has_privacy_rules(conn, u["id"]) and is_location_suppressed(
                conn, u["id"], u["lat"], u["lng"]
            ):
                continue
            visible_users.append(u)
        users = visible_users
    finally:
        conn.close()

    return {"users": users}


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------

@app.patch("/api/users/me/location")
async def update_location(body: LocationUpdate, current=Depends(get_current_user)):
    user_id = current["id"]
    conn = get_db()
    try:
        conn.execute(
            "UPDATE users SET lat = ?, lng = ?, location_visible = ? WHERE id = ?",
            (body.lat, body.lng, 1 if body.visible else 0, user_id),
        )
        conn.commit()

        suppressed = is_location_suppressed(conn, user_id, body.lat, body.lng)
        if suppressed:
            conn.execute(
                "UPDATE users SET location_visible = 0 WHERE id = ?", (user_id,)
            )
            conn.commit()

        row = fetch_user_row(conn, user_id)
        result = serialize_user(conn, row, include_private=True)
    finally:
        conn.close()

    visible = body.visible and not suppressed
    if visible:
        await broadcast(
            {
                "event": "location_update",
                "userId": user_id,
                "lat": body.lat,
                "lng": body.lng,
            },
            exclude=user_id,
        )
    else:
        await broadcast({"event": "user_hidden", "userId": user_id}, exclude=user_id)

    if suppressed:
        result["locationVisible"] = False
        result["suppressed"] = True
    return result


# ---------------------------------------------------------------------------
# Privacy — blackout zones & schedule
# ---------------------------------------------------------------------------

@app.get("/api/privacy/blackout")
def list_blackout(current=Depends(get_current_user)):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM blackout_zones WHERE user_id = ?", (current["id"],)
        ).fetchall()
    finally:
        conn.close()
    return {
        "zones": [
            {
                "id": r["id"],
                "label": r["label"],
                "centerLat": r["center_lat"],
                "centerLng": r["center_lng"],
                "radiusMiles": r["radius_miles"],
            }
            for r in rows
        ]
    }


@app.post("/api/privacy/blackout")
def add_blackout(body: BlackoutZoneBody, current=Depends(get_current_user)):
    zone_id = str(uuid.uuid4())
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO blackout_zones (id, user_id, label, center_lat, center_lng, radius_miles) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (zone_id, current["id"], body.label, body.centerLat, body.centerLng, body.radiusMiles),
        )
        conn.commit()
    finally:
        conn.close()
    return {
        "id": zone_id,
        "label": body.label,
        "centerLat": body.centerLat,
        "centerLng": body.centerLng,
        "radiusMiles": body.radiusMiles,
    }


@app.delete("/api/privacy/blackout/{zone_id}")
def delete_blackout(zone_id: str, current=Depends(get_current_user)):
    conn = get_db()
    try:
        conn.execute(
            "DELETE FROM blackout_zones WHERE id = ? AND user_id = ?",
            (zone_id, current["id"]),
        )
        conn.commit()
    finally:
        conn.close()
    return {"success": True}


@app.get("/api/privacy/schedule")
def get_schedule(current=Depends(get_current_user)):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM location_schedules WHERE user_id = ?", (current["id"],)
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return {"shareFrom": "08:00", "shareUntil": "22:00", "enabled": False}
    return {
        "shareFrom": row["share_from"],
        "shareUntil": row["share_until"],
        "enabled": bool(row["enabled"]),
    }


@app.put("/api/privacy/schedule")
def put_schedule(body: ScheduleBody, current=Depends(get_current_user)):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO location_schedules (user_id, share_from, share_until, enabled) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET share_from = excluded.share_from, "
            "share_until = excluded.share_until, enabled = excluded.enabled",
            (current["id"], body.shareFrom, body.shareUntil, 1 if body.enabled else 0),
        )
        conn.commit()
    finally:
        conn.close()
    return {"shareFrom": body.shareFrom, "shareUntil": body.shareUntil, "enabled": body.enabled}


# ---------------------------------------------------------------------------
# Connections
# ---------------------------------------------------------------------------

def find_thread(conn, a: str, b: str):
    lo, hi = pair(a, b)
    return conn.execute(
        "SELECT * FROM chat_threads WHERE user_a = ? AND user_b = ?", (lo, hi)
    ).fetchone()


@app.post("/api/connections/request")
async def create_connection_request(
    body: ConnectionRequestBody, current=Depends(get_current_user)
):
    if body.toUserId == current["id"]:
        raise HTTPException(status_code=400, detail="Cannot connect with yourself")
    conn = get_db()
    try:
        target = fetch_user_row(conn, body.toUserId)
        if target is None:
            raise HTTPException(status_code=404, detail="User not found")

        # Already connected?
        if find_thread(conn, current["id"], body.toUserId):
            raise HTTPException(status_code=400, detail="Already connected")

        # Existing pending request from me?
        pending = conn.execute(
            "SELECT id FROM connection_requests WHERE from_id = ? AND to_id = ? AND status = 'pending'",
            (current["id"], body.toUserId),
        ).fetchone()
        if pending:
            raise HTTPException(status_code=400, detail="Request already pending")

        # Cooldown check
        cd = conn.execute(
            "SELECT expires_at FROM connection_cooldowns WHERE from_id = ? AND to_id = ?",
            (current["id"], body.toUserId),
        ).fetchone()
        if cd and datetime.fromisoformat(cd["expires_at"]) > now_utc():
            raise HTTPException(
                status_code=400,
                detail="You cannot request this user again yet. Try later.",
            )

        # Proximity check
        me = fetch_user_row(conn, current["id"])
        dist = haversine_miles(me["lat"], me["lng"], target["lat"], target["lng"])
        if dist > PROXIMITY_LIMIT_MILES:
            raise HTTPException(
                status_code=400,
                detail="This user is out of range. Get closer to connect.",
            )

        request_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO connection_requests (id, from_id, to_id, intro_message, status) "
            "VALUES (?, ?, ?, ?, 'pending')",
            (request_id, current["id"], body.toUserId, body.introMessage),
        )
        conn.commit()
        from_user = serialize_user(conn, me)
    finally:
        conn.close()

    await push(
        body.toUserId,
        {
            "event": "connection_request",
            "requestId": request_id,
            "fromUser": from_user,
            "introMessage": body.introMessage,
        },
    )
    return {"id": request_id, "status": "pending"}


@app.get("/api/connections/requests/inbox")
def inbox(current=Depends(get_current_user)):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM connection_requests WHERE to_id = ? AND status = 'pending' "
            "ORDER BY created_at DESC",
            (current["id"],),
        ).fetchall()
        requests = []
        for r in rows:
            sender = fetch_user_row(conn, r["from_id"])
            if sender is None:
                continue
            requests.append(
                {
                    "id": r["id"],
                    "introMessage": r["intro_message"],
                    "createdAt": r["created_at"],
                    "fromUser": serialize_user(conn, sender),
                }
            )
        return {"requests": requests}
    finally:
        conn.close()


@app.patch("/api/connections/requests/{request_id}")
async def decide_request(
    request_id: str, body: ConnectionDecision, current=Depends(get_current_user)
):
    conn = get_db()
    try:
        req = conn.execute(
            "SELECT * FROM connection_requests WHERE id = ?", (request_id,)
        ).fetchone()
        if req is None:
            raise HTTPException(status_code=404, detail="Request not found")
        if req["to_id"] != current["id"]:
            raise HTTPException(status_code=403, detail="Not your request to decide")
        if req["status"] != "pending":
            raise HTTPException(status_code=400, detail="Request already resolved")

        from_id, to_id = req["from_id"], req["to_id"]

        if body.accepted:
            conn.execute(
                "UPDATE connection_requests SET status = 'accepted' WHERE id = ?",
                (request_id,),
            )
            thread = find_thread(conn, from_id, to_id)
            if thread is None:
                thread_id = str(uuid.uuid4())
                lo, hi = pair(from_id, to_id)
                conn.execute(
                    "INSERT INTO chat_threads (id, user_a, user_b) VALUES (?, ?, ?)",
                    (thread_id, lo, hi),
                )
            else:
                thread_id = thread["id"]
            conn.commit()
            by_user = serialize_user(conn, fetch_user_row(conn, current["id"]))
            await push(
                from_id,
                {
                    "event": "connection_accepted",
                    "requestId": request_id,
                    "threadId": thread_id,
                    "byUser": by_user,
                },
            )
            return {"status": "accepted", "threadId": thread_id}
        else:
            conn.execute(
                "UPDATE connection_requests SET status = 'declined' WHERE id = ?",
                (request_id,),
            )
            expires = (now_utc() + timedelta(hours=COOLDOWN_HOURS)).isoformat()
            conn.execute(
                "INSERT INTO connection_cooldowns (from_id, to_id, expires_at) VALUES (?, ?, ?) "
                "ON CONFLICT(from_id, to_id) DO UPDATE SET expires_at = excluded.expires_at",
                (from_id, to_id, expires),
            )
            conn.commit()
            await push(
                from_id,
                {"event": "connection_declined", "requestId": request_id},
            )
            return {"status": "declined"}
    finally:
        conn.close()


@app.get("/api/connections")
def list_connections(current=Depends(get_current_user)):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM chat_threads WHERE user_a = ? OR user_b = ?",
            (current["id"], current["id"]),
        ).fetchall()
        connections = []
        for t in rows:
            other_id = t["user_b"] if t["user_a"] == current["id"] else t["user_a"]
            other = fetch_user_row(conn, other_id)
            if other is None:
                continue
            connections.append(
                {
                    "threadId": t["id"],
                    "user": serialize_user(conn, other),
                }
            )

        # Outgoing pending requests so the UI can show "Request Sent"
        pending_rows = conn.execute(
            "SELECT to_id FROM connection_requests WHERE from_id = ? AND status = 'pending'",
            (current["id"],),
        ).fetchall()
        pending = [r["to_id"] for r in pending_rows]
        return {"connections": connections, "pendingTo": pending}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

def thread_for_user(conn, thread_id: str, user_id: str):
    t = conn.execute(
        "SELECT * FROM chat_threads WHERE id = ?", (thread_id,)
    ).fetchone()
    if t is None:
        raise HTTPException(status_code=404, detail="Thread not found")
    if user_id not in (t["user_a"], t["user_b"]):
        raise HTTPException(status_code=403, detail="Not a participant")
    return t


@app.get("/api/chat/threads")
def list_threads(current=Depends(get_current_user)):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM chat_threads WHERE user_a = ? OR user_b = ?",
            (current["id"], current["id"]),
        ).fetchall()
        threads = []
        for t in rows:
            other_id = t["user_b"] if t["user_a"] == current["id"] else t["user_a"]
            other = fetch_user_row(conn, other_id)
            if other is None:
                continue
            last = conn.execute(
                "SELECT * FROM chat_messages WHERE thread_id = ? ORDER BY sent_at DESC LIMIT 1",
                (t["id"],),
            ).fetchone()
            threads.append(
                {
                    "id": t["id"],
                    "user": serialize_user(conn, other),
                    "lastMessage": last["body"] if last else None,
                    "lastMessageAt": last["sent_at"] if last else None,
                }
            )
        threads.sort(key=lambda x: x["lastMessageAt"] or "", reverse=True)
        return {"threads": threads}
    finally:
        conn.close()


@app.get("/api/chat/threads/{thread_id}/messages")
def get_messages(thread_id: str, current=Depends(get_current_user)):
    conn = get_db()
    try:
        thread_for_user(conn, thread_id, current["id"])
        rows = conn.execute(
            "SELECT * FROM chat_messages WHERE thread_id = ? ORDER BY sent_at ASC",
            (thread_id,),
        ).fetchall()
        return {
            "messages": [
                {
                    "id": r["id"],
                    "threadId": r["thread_id"],
                    "fromId": r["from_id"],
                    "body": r["body"],
                    "sentAt": r["sent_at"],
                }
                for r in rows
            ]
        }
    finally:
        conn.close()


def update_streak(conn, user_a: str, user_b: str) -> int:
    lo, hi = pair(user_a, user_b)
    row = conn.execute(
        "SELECT * FROM streaks WHERE user_a = ? AND user_b = ?", (lo, hi)
    ).fetchone()
    now = now_utc()
    if row is None:
        conn.execute(
            "INSERT INTO streaks (id, user_a, user_b, count, last_message_at) VALUES (?, ?, ?, 1, ?)",
            (str(uuid.uuid4()), lo, hi, now.isoformat()),
        )
        return 1
    last = row["last_message_at"]
    if last:
        try:
            last_dt = datetime.fromisoformat(last)
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            last_dt = None
    else:
        last_dt = None
    if last_dt is not None and (now - last_dt) <= timedelta(days=7):
        new_count = row["count"] + 1
    else:
        new_count = 1
    conn.execute(
        "UPDATE streaks SET count = ?, last_message_at = ? WHERE user_a = ? AND user_b = ?",
        (new_count, now.isoformat(), lo, hi),
    )
    return new_count


@app.post("/api/chat/threads/{thread_id}/messages")
async def send_message(
    thread_id: str, body: MessageBody, current=Depends(get_current_user)
):
    conn = get_db()
    try:
        t = thread_for_user(conn, thread_id, current["id"])
        other_id = t["user_b"] if t["user_a"] == current["id"] else t["user_a"]
        message_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO chat_messages (id, thread_id, from_id, body) VALUES (?, ?, ?, ?)",
            (message_id, thread_id, current["id"], body.body),
        )
        update_streak(conn, current["id"], other_id)
        conn.commit()
        saved = conn.execute(
            "SELECT * FROM chat_messages WHERE id = ?", (message_id,)
        ).fetchone()
        message = {
            "id": saved["id"],
            "threadId": saved["thread_id"],
            "fromId": saved["from_id"],
            "body": saved["body"],
            "sentAt": saved["sent_at"],
        }
    finally:
        conn.close()

    await push(other_id, {"event": "chat_message", "threadId": thread_id, "message": message})
    return message


# ---------------------------------------------------------------------------
# Streaks / Leaderboard
# ---------------------------------------------------------------------------

@app.get("/api/streaks")
def get_streaks(current=Depends(get_current_user)):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM streaks WHERE user_a = ? OR user_b = ?",
            (current["id"], current["id"]),
        ).fetchall()
        result = []
        for r in rows:
            other_id = r["user_b"] if r["user_a"] == current["id"] else r["user_a"]
            other = fetch_user_row(conn, other_id)
            if other is None:
                continue
            result.append(
                {
                    "count": r["count"],
                    "lastMessageAt": r["last_message_at"],
                    "user": serialize_user(conn, other),
                }
            )
        result.sort(key=lambda x: x["count"], reverse=True)
        return {"streaks": result}
    finally:
        conn.close()


@app.get("/api/leaderboard")
def leaderboard():
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM users").fetchall()
        entries = []
        for u in rows:
            best = conn.execute(
                "SELECT MAX(count) AS best FROM streaks WHERE user_a = ? OR user_b = ?",
                (u["id"], u["id"]),
            ).fetchone()
            entries.append(
                {
                    "id": u["id"],
                    "displayName": u["display_name"],
                    "photoUrl": u["photo_url"],
                    "streak": best["best"] or 0,
                }
            )
        entries.sort(key=lambda x: x["streak"], reverse=True)
        for i, e in enumerate(entries[:50], start=1):
            e["rank"] = i
        return {"leaderboard": entries[:50]}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, token: str | None = None):
    # Authenticate via ?token= query param before accepting.
    try:
        token_user = decode_token(token) if token else None
    except HTTPException:
        token_user = None
    if token_user is None or token_user != user_id:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    connected_clients[user_id] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
            except (ValueError, TypeError):
                continue
            if msg.get("event") == "location_update":
                lat, lng = msg.get("lat"), msg.get("lng")
                visible = msg.get("visible")
                if lat is None or lng is None:
                    continue
                conn = get_db()
                try:
                    if visible is None:
                        conn.execute(
                            "UPDATE users SET lat = ?, lng = ? WHERE id = ?",
                            (lat, lng, user_id),
                        )
                    else:
                        conn.execute(
                            "UPDATE users SET lat = ?, lng = ?, location_visible = ? WHERE id = ?",
                            (lat, lng, 1 if visible else 0, user_id),
                        )
                    conn.commit()

                    suppressed = is_location_suppressed(conn, user_id, lat, lng)
                    if suppressed:
                        conn.execute(
                            "UPDATE users SET location_visible = 0 WHERE id = ?",
                            (user_id,),
                        )
                        conn.commit()
                finally:
                    conn.close()

                if suppressed or visible is False:
                    await broadcast(
                        {"event": "user_hidden", "userId": user_id},
                        exclude=user_id,
                    )
                else:
                    await broadcast(
                        {
                            "event": "location_update",
                            "userId": user_id,
                            "lat": lat,
                            "lng": lng,
                        },
                        exclude=user_id,
                    )
    except WebSocketDisconnect:
        connected_clients.pop(user_id, None)
        await broadcast({"event": "user_offline", "userId": user_id})
    except Exception:
        connected_clients.pop(user_id, None)
