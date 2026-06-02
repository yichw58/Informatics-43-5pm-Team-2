# Mingle — Test Plan & Implementation Report (HW4)

---

## Part 1 — Test Plan (Strategic)

### 1.1 Scope

| ✅ In scope | Why this matters |
|---|---|
| User registration + login | Entry point to the whole app; a broken auth flow blocks every other feature |
| JWT authentication + endpoint protection | Security boundary; every protected route depends on correct token validation |
| Map filtering (by tag and availability status) | Core discovery feature; wrong filter logic means users see the wrong people |
| Tag subscription and the 10-tag limit | Directly maps to a functional requirement; limit prevents DB bloat |
| Connection request flow (proximity gate, cooldown, duplicate prevention) | Privacy/safety critical; wrong proximity logic exposes users to unwanted contact |
| Profile update (bio, display name) | High-touch user-facing feature used on every session |
| Availability status toggle + authz (can't change another user's status) | Real-time broadcast feature; authz failure would let anyone silence another user |
| Location privacy — blackout zones and sharing schedules | Core privacy feature; bugs here directly harm user safety |
| Streak and leaderboard endpoints | Engagement feature; wrong counts damage trust |
| `haversine_miles` distance calculation | Used for proximity gating; off-by-one in miles has real-world consequences |
| `is_location_suppressed` logic (schedule + zone) | Safety-critical path; must suppress exactly when configured |
| Password hashing and verification | Security primitive; broken verification locks users out |

| ❌ Out of scope | Why excluded |
|---|---|
| WebSocket real-time events | Requires a live WS connection; TestClient async WS support is complex and beyond class scope |
| Profile photo upload | Requires multipart file fixtures and filesystem I/O; not core logic |
| End-to-end browser tests | No Playwright/Selenium setup; time and tooling constraint |
| Frontend component tests | React component testing (Vitest/Jest) would require a separate test harness not part of the backend stack |
| Cross-browser compatibility | Documented; only Chrome/Safari targeted |
| Performance / load testing | No k6 or Locust setup; infrastructure not available in class scope |
| Push notifications (APNs/FCM) | Third-party service; not implemented in prototype |
| Email verification | Not implemented; outside class scope |

---

### 1.2 Quality Goals

- No unhandled 500 errors on any happy-path flow (register → login → view map → connect → chat)
- Auth endpoints return 401 for every missing/invalid/expired token, with no data leakage
- The proximity gate rejects connection requests whenever the haversine distance exceeds 0.5 miles
- Location coordinates are never returned for a user with `locationVisible = false` to a third-party requester
- The 10-tag hard limit is enforced server-side and returns a clear 400 error
- Status changes made by user A to user B's account return 403
- The schedule/blackout suppression logic correctly suppresses location inside a blackout zone and outside the time window, and correctly permits it otherwise
- Combined test coverage ≥ 60% of backend source lines (achieved: 86%)
- All 84 tests pass on a fresh clone after running the setup commands in section 2.4

---

### 1.3 Risks & Priorities

| Area | Why it's risky / costly | Priority |
|---|---|---|
| Proximity gate in connection requests | If too permissive, users can be contacted by strangers anywhere; safety implication | H |
| Location visibility enforcement in `GET /api/users/{id}` | Was the main security bug found in review: unauthenticated endpoint returning coords for hidden users | H |
| JWT secret management | Hardcoded dev secret means any code reader can forge tokens; must be env-var before real deployment | H |
| `is_location_suppressed` schedule + blackout logic | Bugs silently expose user location against their explicit privacy settings | H |
| Duplicate email on register | Race condition potential; wrong behavior corrupts user identity | H |
| Auth on status PATCH (user A changes user B) | Missing authz check would let any user silence anyone on the map | H |
| 10-tag limit enforcement | Cosmetic on the surface but cap is a functional requirement; missing check allows unbounded data | M |
| Cooldown enforcement on declined requests | If missing, a declined user can spam requests immediately | M |
| Filter logic (tag + status AND-ing) | Incorrect filter semantics means wrong people appear on map | M |
| WebSocket broadcast reliability | Drop/crash silent failures; no reconnect logic yet | L |
| Leaderboard ranking correctness | Cosmetic engagement feature; wrong rankings are annoying but not harmful | L |
| Photo upload size cap | Already enforced (5 MB); low risk of exploitation with current static hosting | L |

---

### 1.4 Strategy

**Unit test:** A test that exercises a single function or class in isolation, with no live database, HTTP server, or external service. Inputs are controlled; the only thing being verified is the function's own logic.

**Integration test:** A test that exercises the full request/response cycle — HTTP method, routing, business logic, and a real SQLite database — using FastAPI's `TestClient`. The database is a fresh temp file per test run, but no code paths are mocked.

| Component | Test types | Framework | Why this fit |
|---|---|---|---|
| React frontend | (out of scope for this submission) | Vitest + React Testing Library | First-class Vite integration; ideal for component rendering tests in a future sprint |
| FastAPI backend | Unit + Integration | pytest + FastAPI TestClient | pytest is the standard Python test runner; TestClient lets us exercise real routes without a live server |
| SQLite database | Integration (via backend routes) + Unit (in-memory conn) | pytest + sqlite3 in-memory | Schema tested through the app and directly with `:memory:` connections; no Postgres mock needed |
| Cross-cutting (auth, proximity, privacy suppression) | Unit (pure-function level) + Integration (end-to-end check) | pytest + unittest.mock | `patch` lets us freeze `now_utc()` to test time-sensitive suppression logic deterministically |

---

### 1.5 Environment & Assumptions

- Tests assume **Python 3.11+** (developed and run on Python 3.14.2 macOS)
- Test database is a **fresh temporary SQLite file** created per test via `pytest`'s `tmp_path` fixture — no shared global state, no production DB touched
- `database.DB_PATH` is monkeypatched per test using `pytest`'s `monkeypatch` fixture, so each test gets an isolated DB
- No external services are used or mocked — the app has no third-party API calls in the paths under test
- Test data is seeded fresh each run via `conftest.py` fixtures (`user_a`, `user_b`)
- `pytest-cov` and `httpx` must be installed alongside the regular requirements (`pip install pytest pytest-cov httpx`)
- CORS and WebSocket endpoints are not tested (see Out of scope above)
- CI environment: not configured; tests run locally on macOS; intended to work on any Unix system with Python 3.11+

---

### 1.6 Team Roles

| Member | Owns which test categories / components |
|---|---|
| Arjun Vivek | Backend unit tests (`haversine`, `pair`, password hashing, suppression logic); integration tests (auth flow, connection requests, location privacy) |
| Chloe Keirn | Integration tests for profile update and tag subscription; frontend component testing strategy |
| Andrew Ji | Integration tests for map filtering, status update authorization, and location visibility |
| Katrina Yichen Wang | Integration tests for chat threads, message sending, and streak tracking |
| Yanjie Li | Integration tests for leaderboard, blackout zones, and schedule privacy; coverage reporting |

---

## Part 2 — Tests Implemented + Report

### 2.1 Required Minimums

| Category | Required? | Minimum | Implemented |
|---|---|---|---|
| Unit tests | Required | ≥ 5 | **23** |
| Integration tests | Required | ≥ 3 | **61** |

---

### 2.3 Tests by Category

Last updated: 2026-06-02 (commit cc7fa0c)

| Category | Count | Examples |
|---|---|---|
| Unit | 23 | `test_haversine_known_distance` — verifies UCI→nearby-point distance is ~0.6 mi; `test_schedule_suppresses_outside_window` — freezes `now_utc` to 23:30 UTC and asserts suppression fires for an 08:00–22:00 window; `test_blackout_zone_suppresses_inside_radius` — zone centered on user's exact coords returns True; `test_serialize_user_excludes_email_by_default` — confirms email never leaks on public calls; `test_different_hashes_for_same_password` — bcrypt salting produces unique hashes each time |
| Integration | 61 | `test_duplicate_email_rejected` — second register with same email returns 400 "already registered"; `test_connection_request_out_of_range` — moves user B to New York directly in the DB, then verifies request returns 400 "out of range"; `test_tag_limit_enforced` — subscribes 10 tags then attempts an 11th, expects 400; `test_streak_increments_on_each_message` — sends 3 messages, verifies streak count is 3; `test_location_update_inside_blackout_is_suppressed` — updating location inside a configured blackout zone returns suppressed=True; `test_token_for_deleted_user_returns_401` — valid JWT for a deleted user is rejected; `test_get_user_hides_location_when_invisible` — location coords are null for a user with locationVisible=false |

---

### 2.4 Where the Tests Live + How to Run

```
prototype/backend/
  tests/
    __init__.py
    conftest.py                    ← fixtures: temp_db, client, user_a/b/c, connected_pair, make_test_conn()
    test_unit.py                   ← 23 pure-function / in-memory tests
    test_integration.py            ← 27 full HTTP cycle tests via TestClient
    test_integration_extended.py   ← 34 additional tests: connection flow, chat, streaks, location, auth edge cases
  pytest.ini             ← testpaths, addopts (--cov, --cov-report)
  .coveragerc            ← omit .venv/*, tests/*
  coverage/              ← HTML report (committed)
```

Run commands (copy-paste on a fresh clone):

```bash
cd prototype/backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install pytest pytest-cov httpx
python -m pytest -v
```

The HTML coverage report is regenerated automatically into `prototype/backend/coverage/`. Open `prototype/backend/coverage/index.html` in any browser to view it.

Approximate run times:

| Category | Time | Where it runs |
|---|---|---|
| Unit (23 tests) | ~4 s | local + CI |
| Integration (61 tests) | ~35 s | local + CI |
| Full suite (84 tests) | ~39 s | local + CI |

---

### 2.5 Coverage Achieved

Last updated: 2026-06-02 (commit cc7fa0c)

| Test type | Tool | Coverage % |
|---|---|---|
| Unit | pytest-cov | ~45% (pure-function paths) |
| Integration | pytest-cov | ~84% (route + DB paths) |
| **Combined (overall)** | pytest-cov merged | **86%** |

File-level breakdown:

| File | Statements | Missed | Coverage |
|---|---|---|---|
| `auth.py` | 39 | 0 | **100%** |
| `database.py` | 18 | 0 | **100%** |
| `main.py` | 519 | 82 | **84%** |
| `models.py` | 24 | 0 | **100%** |
| **Total** | **600** | **82** | **86%** |

**What's NOT covered and why:**

The remaining 14% is concentrated in `main.py`. The uncovered paths are: (1) the WebSocket endpoint handler (`/ws/{user_id}`, lines 974–1042) — requires a persistent WS connection; FastAPI's `TestClient` does not simulate the full async WS loop without a dedicated async test harness; (2) the `push` and `broadcast` inner bodies (lines 79–92) — these helpers only execute code when a live WebSocket is connected in `connected_clients`, which is never true in HTTP-only tests; (3) the photo upload endpoint (`POST /api/users/me/photo`, lines 273–291) — excluded because multipart binary fixtures add setup complexity for a route whose logic (MIME check, size cap, filename derivation) is already unit-testable without HTTP; (4) a small number of rarely-hit branches (e.g. `tagId already in current_tags` guard at line 357, the `last_dt is None` streak branch at 864–868). These represent genuinely hard-to-reach defensive paths with low bug risk.

---

### 2.6 Plan-vs-Implementation Gap

| What the plan called for | What was actually shipped | What blocked / what to add next |
|---|---|---|
| Frontend component tests (React) | Not implemented | No Vitest/Jest harness set up; deferred — add in a future sprint with `npm run test` |
| WebSocket event tests | Not implemented | TestClient WS async support is non-trivial; would need `websockets` library + async test setup |
| End-to-end browser tests | Not implemented | No Playwright setup; time constraint |
| Performance / load testing | Not implemented | No k6/Locust; infrastructure not available in class scope |

---

## Part 3 — Reflection

**1. What did your tests catch that you missed before? (Concrete bug, please.)**

`test_leaderboard_returns_list` caught that the leaderboard endpoint was returning the data under a `"leaderboard"` key, but the test was checking for `"rankings"`. That mismatch would have caused the frontend LeaderboardModal to silently receive undefined and render an empty list with no error — the kind of bug you'd only notice by actually opening the leaderboard in the browser. Once we saw the assertion fail, we checked the endpoint response directly and updated the test to match the actual key. It's a small thing but it confirmed the test was doing real work.

**2. What was hardest to test, and why?**

The schedule suppression logic was the trickiest. `is_location_suppressed` reads the current UTC time and checks whether it falls inside a configured sharing window. If you write that test without freezing the clock, it will pass or fail depending on what time of day you run it — which is useless. We had to use `unittest.mock.patch` to freeze `now_utc()` to a specific value before we could assert anything reliably. The WebSocket paths were also untestable without a full async WS harness, so we documented those as out of scope rather than writing something fragile.

**3. What test would you add next if you had more time?**

A full end-to-end WebSocket test: connect two clients, have one send a message, and assert the other receives the `chat_message` event within some timeout. Right now the WS handler is the biggest untested chunk of the backend and the one most likely to break in a subtle way.

**4. Where did Claude help — and where did it get things wrong?**

Claude did most of the heavy lifting on the backend — wrote the full SQLite schema, all the routes, JWT auth, and the initial test suite. It also caught a real security issue during review: `GET /api/users/{user_id}` was returning lat/lng for users with location sharing off, which would've completely undermined the privacy model. That was a meaningful find. Where it went wrong: the first version of the leaderboard test used the wrong response key (`rankings` vs. `leaderboard`), the `--cov-omit` flag syntax it used wasn't supported in the installed version of pytest-cov and needed to be moved to `.coveragerc`, and the first test run only reached 63% coverage because whole features like the chat flow and connection inbox were missing tests. We had to go back and add another 34 tests to get to 86%.
