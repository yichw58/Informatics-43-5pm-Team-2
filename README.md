# Mingle

A location-based social discovery app — find people nearby who share your interests, connect, and chat in real time.

## Prerequisites
- Python 3.9+
- Node.js 18+

---

## Running the app

### 1. Start the backend

```bash
cd prototype/backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The API runs at `http://localhost:8000`. A `mingle.db` SQLite file is created automatically on first run.

### 2. Start the frontend

In a separate terminal:

```bash
cd prototype/frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## What's in the app

**Create an account / Log in** — Register with a display name, email, and password. Your session persists across page reloads.

**Map** — See nearby users as pins. Green pins are open to meet; gray pins are busy. Click any pin to view their profile.

**Status toggle** — Switch between "Open to Meet" and "Busy" from the nav bar. Updates are broadcast in real time.

**Filters** — Filter visible users by interest tags and/or availability status. Filters reset on page reload.

**Connect** — Click a user's pin and send a connection request (with an optional intro message). The other user accepts or declines from their request inbox (🔔).

**Chat** — Once connected, open a private chat thread from the 💬 button. Messages are delivered in real time via WebSocket.

**Profile** — Click your avatar to edit your display name, bio, interests, and location sharing settings (blackout zones and time schedules).

**Leaderboard** — Click 🏆 to see the streak leaderboard. A streak increments each time you send a message; it resets after 7 days of inactivity.

---

## Running the tests

```bash
cd prototype/backend
source .venv/bin/activate
pip install pytest pytest-cov httpx
python -m pytest -v
```

84 tests, ~39 seconds. Coverage report is written to `prototype/backend/coverage/index.html`.

---

## Notes
- All data persists in `prototype/backend/mingle.db`. Delete this file to reset to a clean state.
- The JWT secret is hardcoded (`mingle-dev-secret-2024`) — fine for local development; must be changed before any real deployment.
- Both servers must be running at the same time for the app to work.
