import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "mingle.db")

SEED_TAGS = [
    ("basketball", "basketball", "🏀", "sports"),
    ("tennis", "tennis", "🎾", "sports"),
    ("hiking", "hiking", "🥾", "sports"),
    ("yoga", "yoga", "🧘", "sports"),
    ("biking", "biking", "🚴", "sports"),
    ("surfing", "surfing", "🏄", "sports"),
    ("coffee", "coffee", "☕", "social"),
    ("chess", "chess", "♟️", "social"),
    ("gaming", "gaming", "🎮", "social"),
    ("music", "music", "🎵", "social"),
    ("photography", "photography", "📷", "social"),
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS tags (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  emoji TEXT DEFAULT '',
  category TEXT DEFAULT 'social'
);

CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  display_name TEXT NOT NULL,
  bio TEXT DEFAULT '',
  photo_url TEXT DEFAULT NULL,
  password_hash TEXT NOT NULL,
  status TEXT DEFAULT 'busy',
  lat REAL DEFAULT 33.6405,
  lng REAL DEFAULT -117.8443,
  location_visible INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS user_tags (
  user_id TEXT,
  tag_id TEXT,
  PRIMARY KEY (user_id, tag_id)
);

CREATE TABLE IF NOT EXISTS connection_requests (
  id TEXT PRIMARY KEY,
  from_id TEXT NOT NULL,
  to_id TEXT NOT NULL,
  intro_message TEXT DEFAULT '',
  status TEXT DEFAULT 'pending',
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS connection_cooldowns (
  from_id TEXT,
  to_id TEXT,
  expires_at TEXT,
  PRIMARY KEY (from_id, to_id)
);

CREATE TABLE IF NOT EXISTS chat_threads (
  id TEXT PRIMARY KEY,
  user_a TEXT NOT NULL,
  user_b TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chat_messages (
  id TEXT PRIMARY KEY,
  thread_id TEXT NOT NULL,
  from_id TEXT NOT NULL,
  body TEXT NOT NULL,
  sent_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS streaks (
  id TEXT PRIMARY KEY,
  user_a TEXT NOT NULL,
  user_b TEXT NOT NULL,
  count INTEGER DEFAULT 0,
  last_message_at TEXT DEFAULT NULL,
  UNIQUE(user_a, user_b)
);

CREATE TABLE IF NOT EXISTS blackout_zones (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  label TEXT DEFAULT 'Home',
  center_lat REAL NOT NULL,
  center_lng REAL NOT NULL,
  radius_miles REAL DEFAULT 0.2
);

CREATE TABLE IF NOT EXISTS location_schedules (
  user_id TEXT PRIMARY KEY,
  share_from TEXT DEFAULT '08:00',
  share_until TEXT DEFAULT '22:00',
  enabled INTEGER DEFAULT 0
);
"""


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    try:
        conn.executescript(SCHEMA)
        for tag_id, name, emoji, category in SEED_TAGS:
            conn.execute(
                "INSERT OR IGNORE INTO tags (id, name, emoji, category) VALUES (?, ?, ?, ?)",
                (tag_id, name, emoji, category),
            )
        conn.commit()
    finally:
        conn.close()
