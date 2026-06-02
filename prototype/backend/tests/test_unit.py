"""
Unit tests for pure helper functions in main.py and auth.py.
No HTTP client, no full app — just function-level correctness.
"""
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from auth import hash_password, verify_password
from main import (
    haversine_miles,
    has_privacy_rules,
    is_location_suppressed,
    pair,
    serialize_user,
)
from tests.conftest import make_test_conn


# ---------------------------------------------------------------------------
# haversine_miles
# ---------------------------------------------------------------------------

def test_haversine_same_point():
    """Distance from a point to itself is zero."""
    assert haversine_miles(33.6405, -117.8443, 33.6405, -117.8443) == pytest.approx(0.0)


def test_haversine_known_distance():
    """UCI Ring Road to a point ~0.6 miles north — value cross-checked with
    a reference implementation."""
    uci = (33.6405, -117.8443)
    north = (33.6492, -117.8443)  # ~0.60 miles
    dist = haversine_miles(*uci, *north)
    assert 0.55 < dist < 0.65


def test_haversine_long_distance():
    """Los Angeles to New York is roughly 2,450 miles."""
    dist = haversine_miles(34.0522, -118.2437, 40.7128, -74.0060)
    assert 2400 < dist < 2500


def test_haversine_symmetry():
    """Distance A→B equals B→A."""
    a = (33.6405, -117.8443)
    b = (33.6492, -117.8490)
    assert haversine_miles(*a, *b) == pytest.approx(haversine_miles(*b, *a))


# ---------------------------------------------------------------------------
# pair
# ---------------------------------------------------------------------------

def test_pair_sorts_lexicographically():
    """pair() always returns the lexicographically smaller ID first."""
    lo, hi = pair("zzz", "aaa")
    assert lo == "aaa"
    assert hi == "zzz"


def test_pair_already_sorted():
    lo, hi = pair("aaa", "zzz")
    assert lo == "aaa"
    assert hi == "zzz"


def test_pair_same_value():
    lo, hi = pair("abc", "abc")
    assert lo == hi == "abc"


# ---------------------------------------------------------------------------
# hash_password / verify_password
# ---------------------------------------------------------------------------

def test_hash_and_verify_correct_password():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed) is True


def test_verify_wrong_password_returns_false():
    hashed = hash_password("secret123")
    assert verify_password("wrongpass", hashed) is False


def test_different_hashes_for_same_password():
    """bcrypt salts mean the same password produces different hashes."""
    h1 = hash_password("password")
    h2 = hash_password("password")
    assert h1 != h2
    assert verify_password("password", h1)
    assert verify_password("password", h2)


# ---------------------------------------------------------------------------
# is_location_suppressed — schedule
# ---------------------------------------------------------------------------

def test_suppression_no_rules():
    """User with no schedule or zones is never suppressed."""
    conn = make_test_conn()
    assert is_location_suppressed(conn, "user1", 33.64, -117.84) is False


def test_suppression_null_coords():
    """None lat/lng short-circuits to False (no location to suppress)."""
    conn = make_test_conn()
    assert is_location_suppressed(conn, "user1", None, None) is False


def test_schedule_suppresses_outside_window():
    """Location is suppressed when the current UTC time is outside share window."""
    conn = make_test_conn()
    conn.execute(
        "INSERT INTO location_schedules (user_id, share_from, share_until, enabled) VALUES (?, ?, ?, ?)",
        ("u1", "08:00", "22:00", 1),
    )
    conn.commit()
    # Freeze time at 23:30 UTC — outside 08:00–22:00
    frozen = datetime(2025, 6, 1, 23, 30, tzinfo=timezone.utc)
    with patch("main.now_utc", return_value=frozen):
        assert is_location_suppressed(conn, "u1", 33.64, -117.84) is True


def test_schedule_allows_inside_window():
    """Location is NOT suppressed when current UTC time is inside the window."""
    conn = make_test_conn()
    conn.execute(
        "INSERT INTO location_schedules (user_id, share_from, share_until, enabled) VALUES (?, ?, ?, ?)",
        ("u1", "08:00", "22:00", 1),
    )
    conn.commit()
    # Freeze time at 12:00 UTC — inside 08:00–22:00
    frozen = datetime(2025, 6, 1, 12, 0, tzinfo=timezone.utc)
    with patch("main.now_utc", return_value=frozen):
        assert is_location_suppressed(conn, "u1", 33.64, -117.84) is False


def test_schedule_disabled_does_not_suppress():
    """A schedule with enabled=0 never suppresses, even outside the window."""
    conn = make_test_conn()
    conn.execute(
        "INSERT INTO location_schedules (user_id, share_from, share_until, enabled) VALUES (?, ?, ?, ?)",
        ("u1", "08:00", "22:00", 0),
    )
    conn.commit()
    frozen = datetime(2025, 6, 1, 23, 30, tzinfo=timezone.utc)
    with patch("main.now_utc", return_value=frozen):
        assert is_location_suppressed(conn, "u1", 33.64, -117.84) is False


# ---------------------------------------------------------------------------
# is_location_suppressed — blackout zones
# ---------------------------------------------------------------------------

def test_blackout_zone_suppresses_inside_radius():
    """User inside a blackout zone should be suppressed."""
    conn = make_test_conn()
    import uuid
    zone_id = str(uuid.uuid4())
    # Zone centered at exactly the user's coords, radius 0.5 miles
    conn.execute(
        "INSERT INTO blackout_zones (id, user_id, label, center_lat, center_lng, radius_miles) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (zone_id, "u1", "Home", 33.64, -117.84, 0.5),
    )
    conn.commit()
    assert is_location_suppressed(conn, "u1", 33.64, -117.84) is True


def test_blackout_zone_allows_outside_radius():
    """User outside the blackout zone radius is not suppressed."""
    conn = make_test_conn()
    import uuid
    zone_id = str(uuid.uuid4())
    # Zone centered at UCI, radius 0.1 miles — user is 5 miles away
    conn.execute(
        "INSERT INTO blackout_zones (id, user_id, label, center_lat, center_lng, radius_miles) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (zone_id, "u1", "Home", 33.64, -117.84, 0.1),
    )
    conn.commit()
    # User at a point ~5 miles away
    assert is_location_suppressed(conn, "u1", 33.70, -117.84) is False


# ---------------------------------------------------------------------------
# has_privacy_rules
# ---------------------------------------------------------------------------

def test_has_privacy_rules_no_rules():
    conn = make_test_conn()
    assert has_privacy_rules(conn, "u1") is False


def test_has_privacy_rules_with_schedule():
    conn = make_test_conn()
    conn.execute(
        "INSERT INTO location_schedules (user_id, share_from, share_until, enabled) VALUES (?, ?, ?, ?)",
        ("u1", "08:00", "22:00", 1),
    )
    conn.commit()
    assert has_privacy_rules(conn, "u1") is True


def test_has_privacy_rules_with_zone():
    conn = make_test_conn()
    import uuid
    conn.execute(
        "INSERT INTO blackout_zones (id, user_id, label, center_lat, center_lng, radius_miles) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), "u1", "Home", 33.64, -117.84, 0.2),
    )
    conn.commit()
    assert has_privacy_rules(conn, "u1") is True


# ---------------------------------------------------------------------------
# serialize_user
# ---------------------------------------------------------------------------

def test_serialize_user_excludes_email_by_default():
    """email should not appear in a public serialize_user call."""
    conn = make_test_conn()
    import uuid
    user_id = str(uuid.uuid4())
    from auth import hash_password as hp
    conn.execute(
        "INSERT INTO users (id, email, display_name, password_hash) VALUES (?, ?, ?, ?)",
        (user_id, "private@test.com", "Test", hp("pw")),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    result = serialize_user(conn, row, include_private=False)
    assert "email" not in result
    assert result["displayName"] == "Test"


def test_serialize_user_includes_email_when_private():
    conn = make_test_conn()
    import uuid
    from auth import hash_password as hp
    user_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO users (id, email, display_name, password_hash) VALUES (?, ?, ?, ?)",
        (user_id, "private@test.com", "Test", hp("pw")),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    result = serialize_user(conn, row, include_private=True)
    assert result["email"] == "private@test.com"
