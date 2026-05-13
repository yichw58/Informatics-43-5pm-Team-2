# Running the Mingle Prototype


## 1. Start the backend

```bash
cd prototype/backend
pip install -r requirements.txt
uvicorn main:app --reload
```

The API will be running at `http://localhost:8000`.

## 2. Start the frontend

In a separate terminal:

```bash
cd prototype/frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## What to try

**Map** — Five seeded users appear as pins near UCI. Blue pin is you.

**Status toggle** — Use the "Open to Meet / Busy" buttons in the top bar to change your status. Green pins are open, gray are busy.

**Filter panel** — Click "⚙ Filters" to open the panel. Select one or more interest tags (e.g. #hiking, #basketball) to show only users with those interests. Combine with a status filter to narrow further. Filters reset on page reload.

**Profile view** — Click any pin on the map to see that user's name, bio, status, and interests.

---

## Notes
- Backend state is in-memory — data resets when the server restarts.
- Both servers must be running at the same time for the app to work.
