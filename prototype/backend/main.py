from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json

app = FastAPI(title="Mingle API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Seed data — all coordinates near UCI campus
# ---------------------------------------------------------------------------

TAGS = [
    {"id": "basketball", "name": "basketball", "emoji": "🏀", "category": "sports"},
    {"id": "tennis",     "name": "tennis",     "emoji": "🎾", "category": "sports"},
    {"id": "hiking",     "name": "hiking",     "emoji": "🥾", "category": "sports"},
    {"id": "yoga",       "name": "yoga",       "emoji": "🧘", "category": "sports"},
    {"id": "biking",     "name": "biking",     "emoji": "🚴", "category": "sports"},
    {"id": "surfing",    "name": "surfing",    "emoji": "🏄", "category": "sports"},
    {"id": "coffee",     "name": "coffee",     "emoji": "☕", "category": "social"},
    {"id": "chess",      "name": "chess",      "emoji": "♟️", "category": "social"},
    {"id": "gaming",     "name": "gaming",     "emoji": "🎮", "category": "social"},
    {"id": "music",      "name": "music",      "emoji": "🎵", "category": "social"},
    {"id": "photography","name": "photography","emoji": "📷", "category": "social"},
]

USERS: dict[str, dict] = {
    "usr_me": {
        "id": "usr_me",
        "displayName": "You",
        "bio": "This is your profile.",
        "photoUrl": None,
        "tags": ["hiking", "basketball"],
        "status": "busy",
        "lat": 33.6405,
        "lng": -117.8443,
        "locationVisible": True,
    },
    "usr_01": {
        "id": "usr_01",
        "displayName": "Alex Chen",
        "bio": "Love exploring trails and capturing moments. Always down for a hike!",
        "photoUrl": None,
        "tags": ["hiking", "photography"],
        "status": "open",
        "lat": 33.6420,
        "lng": -117.8450,
        "locationVisible": True,
    },
    "usr_02": {
        "id": "usr_02",
        "displayName": "Priya Patel",
        "bio": "Chess enthusiast and coffee addict. Let's grab a cup and play a game.",
        "photoUrl": None,
        "tags": ["chess", "coffee"],
        "status": "busy",
        "lat": 33.6380,
        "lng": -117.8430,
        "locationVisible": True,
    },
    "usr_03": {
        "id": "usr_03",
        "displayName": "Marcus Kim",
        "bio": "Pickup basketball every weekend. Also into gaming when I'm indoors.",
        "photoUrl": None,
        "tags": ["basketball", "gaming"],
        "status": "open",
        "lat": 33.6410,
        "lng": -117.8460,
        "locationVisible": True,
    },
    "usr_04": {
        "id": "usr_04",
        "displayName": "Sofia Rodriguez",
        "bio": "Hiker and yogi. Looking for people to join sunrise hikes!",
        "photoUrl": None,
        "tags": ["hiking", "yoga"],
        "status": "open",
        "lat": 33.6395,
        "lng": -117.8420,
        "locationVisible": True,
    },
    "usr_05": {
        "id": "usr_05",
        "displayName": "Jake Thompson",
        "bio": "Musician and coffee lover. Always finding new indie spots.",
        "photoUrl": None,
        "tags": ["coffee", "music"],
        "status": "busy",
        "lat": 33.6430,
        "lng": -117.8410,
        "locationVisible": True,
    },
}

connected_clients: dict[str, WebSocket] = {}


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class StatusUpdate(BaseModel):
    status: str  # "open" | "busy"

class TagAction(BaseModel):
    tagId: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/api/tags")
def get_tags(search: Optional[str] = None, category: Optional[str] = None):
    tags = TAGS
    if search:
        tags = [t for t in tags if search.lower() in t["name"].lower()]
    if category:
        tags = [t for t in tags if t["category"] == category]
    return {"tags": tags}


@app.get("/api/map/users")
def get_map_users(tags: Optional[str] = None, status: Optional[str] = None):
    users = [u for uid, u in USERS.items() if uid != "usr_me" and u["locationVisible"]]

    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if tag_list:
            users = [u for u in users if any(t in u["tags"] for t in tag_list)]

    if status and status != "all":
        users = [u for u in users if u["status"] == status]

    return {"users": users}


@app.get("/api/users/{user_id}")
def get_user(user_id: str):
    user = USERS.get(user_id)
    if not user:
        return {"error": "User not found"}
    return user


@app.patch("/api/users/{user_id}/status")
async def update_status(user_id: str, update: StatusUpdate):
    if user_id not in USERS:
        return {"error": "User not found"}
    USERS[user_id]["status"] = update.status
    event = {"event": "status_update", "userId": user_id, "status": update.status}
    for cid, ws in list(connected_clients.items()):
        try:
            await ws.send_text(json.dumps(event))
        except Exception:
            pass
    return {"success": True, "status": update.status}


@app.post("/api/users/{user_id}/tags/subscribe")
def subscribe_tag(user_id: str, body: TagAction):
    if user_id not in USERS:
        return {"error": "User not found"}
    user = USERS[user_id]
    if len(user["tags"]) >= 10:
        return {"error": "Max 10 tags reached"}
    if body.tagId not in user["tags"]:
        user["tags"].append(body.tagId)
    return {"success": True, "tags": user["tags"]}


@app.delete("/api/users/{user_id}/tags/{tag_id}")
def unsubscribe_tag(user_id: str, tag_id: str):
    if user_id not in USERS:
        return {"error": "User not found"}
    user = USERS[user_id]
    user["tags"] = [t for t in user["tags"] if t != tag_id]
    return {"success": True, "tags": user["tags"]}


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    connected_clients[user_id] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("event") == "location_update" and user_id in USERS:
                USERS[user_id]["lat"] = msg["lat"]
                USERS[user_id]["lng"] = msg["lng"]
                broadcast = {
                    "event": "location_update",
                    "userId": user_id,
                    "lat": msg["lat"],
                    "lng": msg["lng"],
                }
                for cid, ws in list(connected_clients.items()):
                    if cid != user_id:
                        try:
                            await ws.send_text(json.dumps(broadcast))
                        except Exception:
                            pass
    except WebSocketDisconnect:
        connected_clients.pop(user_id, None)
