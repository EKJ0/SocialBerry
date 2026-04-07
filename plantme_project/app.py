from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, abort, jsonify, render_template, request

try:
    # When run as `python -m plantme_project.app`
    from plantme_project import auth as auth_lib
    from plantme_project.db import db_conn, fetch_one, get_db_path, migrate
except ModuleNotFoundError:
    # When run as `python plantme_project/app.py`
    import auth as auth_lib  # type: ignore
    from db import db_conn, fetch_one, get_db_path, migrate  # type: ignore

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
ANXIETY_EVENTS_PATH = DATA_DIR / 'anxiety_events.jsonl'
DB_PATH = get_db_path(BASE_DIR)

app = Flask(__name__)
app.secret_key = os.environ.get("PLANTME_SECRET_KEY", "dev-only-secret-key")


def init_db() -> None:
    with db_conn(DB_PATH) as conn:
        migrate(conn)


init_db()


def load_json(filename: str) -> Any:
    path = DATA_DIR / filename
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(obj, ensure_ascii=False) + '\n')


def read_recent_events(limit: int = 500) -> list[dict[str, Any]]:
    if not ANXIETY_EVENTS_PATH.exists():
        return []
    # Read last N lines without loading huge files (simple approach for MVP).
    with ANXIETY_EVENTS_PATH.open('r', encoding='utf-8') as f:
        lines = f.readlines()[-limit:]
    out: list[dict[str, Any]] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def last_episode_at(events: list[dict[str, Any]]) -> datetime | None:
    for ev in reversed(events):
        if ev.get('type') == 'episode':
            try:
                return datetime.fromisoformat(ev.get('ts'))
            except Exception:
                return None
    return None


def compute_risk_and_patterns(latest: dict[str, Any] | None, events: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Server-side "ML-ish" scoring for MVP:
    - Start with weighted features
    - Personalize a bit via simple frequency-based adjustments from user history
    This keeps outputs explainable and avoids overclaiming exact timing.
    """
    latest = latest or {}
    anxiety_level = float(latest.get('anxiety_level') or 0)
    sleep_hours = latest.get('sleep_hours')
    caffeine_mg = latest.get('caffeine_mg')
    heart_rate_bpm = latest.get('heart_rate_bpm')
    breathing_rate_bpm = latest.get('breathing_rate_bpm')
    context = (latest.get('context') or '').strip().lower()
    stress_event = (latest.get('stress_event') or '').strip().lower()
    food_level = latest.get('food_level')

    score = 0.0
    reasons: list[str] = []

    if anxiety_level >= 8:
        score += 3.0
        reasons.append('high self-reported anxiety')
    elif anxiety_level >= 6:
        score += 2.0
        reasons.append('elevated self-reported anxiety')
    elif anxiety_level >= 4:
        score += 1.0

    if sleep_hours is not None and sleep_hours != '':
        sh = float(sleep_hours)
        if sh < 5.5:
            score += 2.0
            reasons.append('poor sleep')
        elif sh < 6.5:
            score += 1.0

    if caffeine_mg is not None and caffeine_mg != '':
        c = float(caffeine_mg)
        if c >= 300:
            score += 1.5
            reasons.append('high caffeine')
        elif c >= 150:
            score += 0.8

    if food_level is not None and food_level != '':
        fl = float(food_level)
        if fl <= 2:
            score += 1.2
            reasons.append('low food intake')
        elif fl <= 4:
            score += 0.6

    if heart_rate_bpm is not None and heart_rate_bpm != '':
        hr = float(heart_rate_bpm)
        if hr >= 105:
            score += 1.2
            reasons.append('elevated heart rate')
        elif hr >= 90:
            score += 0.6

    if breathing_rate_bpm is not None and breathing_rate_bpm != '':
        br = float(breathing_rate_bpm)
        if br >= 24:
            score += 0.8
            reasons.append('fast breathing rate')

    if stress_event:
        score += 0.8
        reasons.append('recent stress event')

    if context in {'commute', 'public'}:
        score += 0.5
        reasons.append(f'context: {context}')

    ep_at = last_episode_at(events)
    if ep_at:
        hours_since = (datetime.now(timezone.utc) - ep_at).total_seconds() / 3600.0
        if hours_since < 24:
            score += 1.2
            reasons.append('recent episode (last 24h)')
        elif hours_since < 72:
            score += 0.6
            reasons.append('episode within 3 days')

    # Light personalization: if many episodes happened on commute days, increase sensitivity.
    episodes = [e for e in events if e.get('type') == 'episode']
    checkins = [e for e in events if e.get('type') == 'checkin']
    if len(episodes) >= 3 and len(checkins) >= 8:
        commute_checkins = [c for c in checkins if (c.get('payload') or {}).get('context') == 'commute']
        commute_bias = (len(commute_checkins) + 1) / (len(checkins) + 2)
        # If commute contexts are rare overall, don't over-weight; if common, allow a modest bump.
        if context == 'commute' and commute_bias >= 0.25:
            score += 0.5

    def level_from_score(s: float) -> str:
        if s >= 6.0:
            return 'high'
        if s >= 3.5:
            return 'medium'
        return 'low'

    # Next-hour is more sensitive to acute physiological signals.
    next_hour_score = score + (0.8 if (heart_rate_bpm and float(heart_rate_bpm) >= 95) else 0.0)
    next_day_score = max(0.0, score - 0.4)  # slightly smoother

    def explanation_for(level: str, rs: list[str]) -> str:
        if not rs:
            return 'Based on your recent check-in signals.'
        top = ', '.join(rs[:3])
        if level == 'low':
            return f'No strong risk signals detected (notable: {top}).'
        if level == 'medium':
            return f'Some signals linked with higher anxiety for you (notable: {top}).'
        return f'Multiple signals are elevated right now (notable: {top}).'

    patterns: list[str] = []
    if sleep_hours is not None and sleep_hours != '' and float(sleep_hours) < 6.5:
        patterns.append('Higher risk after poor sleep (keep tracking to confirm).')
    if context == 'commute':
        patterns.append('Higher risk on commute days (keep tracking to confirm).')
    if (caffeine_mg not in (None, '') and float(caffeine_mg) >= 150) and (food_level not in (None, '') and float(food_level) <= 4):
        patterns.append('Higher risk after caffeine + low food intake (keep tracking to confirm).')

    # Add a couple inferred patterns from history (very conservative).
    if len(episodes) >= 3:
        commute_episodes = 0
        for ep in episodes[-25:]:
            ctx = (ep.get('context') or '').strip().lower()
            if ctx == 'commute':
                commute_episodes += 1
        if commute_episodes >= 2:
            patterns.append('Episodes have clustered around commute context in your history.')

    return {
        'risk_next_hour': {
            'level': level_from_score(next_hour_score),
            'score': round(next_hour_score, 2),
            'explanation': explanation_for(level_from_score(next_hour_score), reasons),
        },
        'risk_next_day': {
            'level': level_from_score(next_day_score),
            'score': round(next_day_score, 2),
            'explanation': explanation_for(level_from_score(next_day_score), reasons),
        },
        'patterns': patterns,
    }


def normalize_identifier(identifier: str) -> str:
    identifier = (identifier or "").strip()
    identifier = re.sub(r"\s+", "", identifier)
    return identifier.lower()


def require_auth() -> auth_lib.AuthedUser | None:
    token = auth_lib.parse_bearer(request.headers.get("Authorization"))
    if not token:
        return None
    payload = auth_lib.verify_token(app.secret_key, token, max_age_seconds=60 * 60 * 24 * 30)
    if not payload:
        return None
    try:
        return auth_lib.AuthedUser(
            user_id=int(payload["user_id"]),
            role=str(payload["role"]),
            identifier=str(payload["identifier"]),
        )
    except Exception:
        return None


def auth_required_json() -> auth_lib.AuthedUser:
    user = require_auth()
    if not user:
        abort(401)
    return user


def ensure_role(user: auth_lib.AuthedUser, role: str) -> None:
    if user.role != role:
        abort(403)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/features')
def features():
    return render_template('features.html')


@app.route('/roles')
def roles():
    return render_template('roles.html')


@app.route('/dashboard/<role>')
def dashboard(role: str):
    data = load_json('seed_data.json')
    if role == 'client':
        return render_template('dashboard_client.html', client=data['client'], trustablePerson=data['trustablePerson'])
    if role == 'trustablePerson':
        return render_template('dashboard_trustable_person.html', trustablePerson=data['trustablePerson'], clients=data['clients'])
    abort(404)


@app.route('/tasks/<role>')
def tasks(role: str):
    data = load_json('seed_data.json')
    if role == 'client':
        return render_template('tasks_client.html', client=data['client'])
    if role == 'trustablePerson':
        return render_template('tasks_trustable_person.html', trustablePerson=data['trustablePerson'], clients=data['clients'])
    abort(404)


@app.route('/garden')
def garden():
    data = load_json('seed_data.json')
    return render_template('garden.html', garden=data['garden'], client=data['client'])


@app.route('/messages')
def messages():
    data = load_json('seed_data.json')
    return render_template('messages.html', messages=data['messages'], trustablePerson=data['trustablePerson'], client=data['client'])


@app.route('/calm')
def calm_checkin():
    return render_template('calm_checkin.html')


@app.route('/api/anxiety/checkin', methods=['POST'])
def api_anxiety_checkin():
    payload = request.get_json(silent=True) or {}
    if 'anxiety_level' not in payload:
        return jsonify({'error': 'Missing anxiety_level'}), 400

    # Store a normalized payload for later personalization.
    normalized = {
        'anxiety_level': payload.get('anxiety_level'),
        'sleep_hours': payload.get('sleep_hours', None),
        'caffeine_mg': payload.get('caffeine_mg', None),
        'heart_rate_bpm': payload.get('heart_rate_bpm', None),
        'breathing_rate_bpm': payload.get('breathing_rate_bpm', None),
        'stress_event': payload.get('stress_event', ''),
        'context': payload.get('context', ''),
        'food_level': payload.get('food_level', None),
    }
    append_jsonl(ANXIETY_EVENTS_PATH, {'ts': utc_now_iso(), 'type': 'checkin', 'payload': normalized})

    events = read_recent_events()
    result = compute_risk_and_patterns(normalized, events)
    return jsonify(result)


@app.route('/api/anxiety/episode', methods=['POST'])
def api_anxiety_episode():
    # For MVP, logging an episode is a single click with current context inferred as unknown.
    append_jsonl(ANXIETY_EVENTS_PATH, {'ts': utc_now_iso(), 'type': 'episode'})
    events = read_recent_events()

    # Use latest checkin if available to compute updated risk/patterns.
    latest_checkin = None
    for ev in reversed(events):
        if ev.get('type') == 'checkin':
            latest_checkin = ev.get('payload') or {}
            break

    result = compute_risk_and_patterns(latest_checkin, events)
    return jsonify(result)


@app.route("/api/auth/start", methods=["POST"])
def api_auth_start():
    """
    MVP login: accept an identifier (email/phone) + role, return a dev_code.
    In production this would send the code via SMS/email instead.
    """
    body = request.get_json(silent=True) or {}
    identifier = normalize_identifier(body.get("identifier", ""))
    role = body.get("role", "")
    if role not in {"client", "trustablePerson"}:
        return jsonify({"error": "Invalid role"}), 400
    if not identifier:
        return jsonify({"error": "Missing identifier"}), 400

    code = auth_lib.make_dev_code()
    now = auth_lib.utc_now_iso()
    expires = auth_lib.code_expires_at(minutes=10)
    with db_conn(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO auth_codes(identifier, role, code, created_at, expires_at, used_at) VALUES(?,?,?,?,?,NULL)",
            (identifier, role, code, now, expires),
        )

    return jsonify({"ok": True, "dev_code": code, "expires_in_seconds": 600})


@app.route("/api/auth/verify", methods=["POST"])
def api_auth_verify():
    body = request.get_json(silent=True) or {}
    identifier = normalize_identifier(body.get("identifier", ""))
    role = body.get("role", "")
    code = str(body.get("code", "")).strip()
    if role not in {"client", "trustablePerson"}:
        return jsonify({"error": "Invalid role"}), 400
    if not identifier or not code:
        return jsonify({"error": "Missing identifier or code"}), 400

    with db_conn(DB_PATH) as conn:
        row = fetch_one(
            conn,
            """
            SELECT id, identifier, role, code, expires_at, used_at
            FROM auth_codes
            WHERE identifier = ? AND role = ? AND code = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (identifier, role, code),
        )
        if not row:
            return jsonify({"error": "Invalid code"}), 400
        if row["used_at"] is not None:
            return jsonify({"error": "Code already used"}), 400
        try:
            if auth_lib.utc_from_iso(row["expires_at"]) < datetime.now(timezone.utc):
                return jsonify({"error": "Code expired"}), 400
        except Exception:
            return jsonify({"error": "Code expired"}), 400

        conn.execute("UPDATE auth_codes SET used_at = ? WHERE id = ?", (auth_lib.utc_now_iso(), int(row["id"])))

        user = fetch_one(conn, "SELECT id, identifier, role FROM users WHERE identifier = ?", (identifier,))
        if not user:
            conn.execute(
                "INSERT INTO users(identifier, role, created_at) VALUES(?,?,?)",
                (identifier, role, auth_lib.utc_now_iso()),
            )
            user = fetch_one(conn, "SELECT id, identifier, role FROM users WHERE identifier = ?", (identifier,))
        user_id = int(user["id"])

    token = auth_lib.issue_token(
        app.secret_key,
        {"user_id": user_id, "identifier": identifier, "role": role},
    )
    return jsonify({"ok": True, "token": token, "user": {"id": user_id, "identifier": identifier, "role": role}})


@app.route("/api/pairing/invite", methods=["POST"])
def api_pairing_invite():
    user = auth_required_json()
    ensure_role(user, "client")

    now = auth_lib.utc_now_iso()
    expires = auth_lib.code_expires_at(minutes=60 * 24)  # 24h
    code = auth_lib.make_invite_code()

    with db_conn(DB_PATH) as conn:
        migrate(conn)
        # retry a couple times in case of collision
        for _ in range(3):
            try:
                conn.execute(
                    "INSERT INTO invites(code, client_user_id, created_at, expires_at, used_at, used_by_user_id) VALUES(?,?,?,?,NULL,NULL)",
                    (code, user.user_id, now, expires),
                )
                break
            except sqlite3.IntegrityError:
                code = auth_lib.make_invite_code()
        else:
            return jsonify({"error": "Could not create invite"}), 500

    return jsonify({"ok": True, "invite": {"code": code, "expires_in_seconds": 86400}})


@app.route("/api/pairing/accept", methods=["POST"])
def api_pairing_accept():
    user = auth_required_json()
    ensure_role(user, "trustablePerson")

    body = request.get_json(silent=True) or {}
    code = str(body.get("code", "")).strip().upper()
    if not code:
        return jsonify({"error": "Missing code"}), 400

    with db_conn(DB_PATH) as conn:
        migrate(conn)
        invite = fetch_one(conn, "SELECT * FROM invites WHERE code = ?", (code,))
        if not invite:
            return jsonify({"error": "Invalid code"}), 400
        if invite["used_at"] is not None:
            return jsonify({"error": "Invite already used"}), 400
        try:
            if auth_lib.utc_from_iso(invite["expires_at"]) < datetime.now(timezone.utc):
                return jsonify({"error": "Invite expired"}), 400
        except Exception:
            return jsonify({"error": "Invite expired"}), 400

        client_user_id = int(invite["client_user_id"])

        # Create pairing (accepted immediately on code use).
        try:
            conn.execute(
                """
                INSERT INTO pairings(client_user_id, trusted_user_id, status, created_at, accepted_at)
                VALUES(?,?,?,?,?)
                """,
                (client_user_id, user.user_id, "accepted", auth_lib.utc_now_iso(), auth_lib.utc_now_iso()),
            )
        except sqlite3.IntegrityError:
            # Already paired.
            pass

        conn.execute(
            "UPDATE invites SET used_at = ?, used_by_user_id = ? WHERE code = ?",
            (auth_lib.utc_now_iso(), user.user_id, code),
        )

        pairing = fetch_one(
            conn,
            "SELECT id, client_user_id, trusted_user_id, status FROM pairings WHERE client_user_id = ? AND trusted_user_id = ?",
            (client_user_id, user.user_id),
        )

    return jsonify({"ok": True, "pairing": dict(pairing) if pairing else None})


@app.route("/api/pairing/status", methods=["GET"])
def api_pairing_status():
    user = auth_required_json()
    with db_conn(DB_PATH) as conn:
        migrate(conn)
        if user.role == "client":
            rows = conn.execute(
                "SELECT id, client_user_id, trusted_user_id, status, created_at, accepted_at FROM pairings WHERE client_user_id = ?",
                (user.user_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, client_user_id, trusted_user_id, status, created_at, accepted_at FROM pairings WHERE trusted_user_id = ?",
                (user.user_id,),
            ).fetchall()
    return jsonify({"ok": True, "pairings": [dict(r) for r in rows]})


@app.route("/api/onboarding/questions", methods=["GET"])
def api_onboarding_questions():
    auth_required_json()
    # Minimal question set for MVP; client can answer and we store.
    questions = [
        {"id": "baseline_anxiety", "type": "scale_0_10", "prompt": "In the past week, what was your average anxiety level?"},
        {"id": "sleep_goal_hours", "type": "number", "prompt": "How many hours of sleep do you aim for?"},
        {"id": "caffeine_sensitivity", "type": "single_select", "prompt": "How sensitive are you to caffeine?", "options": ["low", "medium", "high"]},
        {"id": "common_contexts", "type": "multi_select", "prompt": "Which contexts are common for you?", "options": ["home", "work", "commute", "public"]},
        {"id": "share_location_default", "type": "single_select", "prompt": "Share location/context with trusted person by default?", "options": ["no", "yes"]},
    ]
    return jsonify({"ok": True, "questions": questions})


@app.route("/api/onboarding/answers", methods=["POST"])
def api_onboarding_answers():
    user = auth_required_json()
    body = request.get_json(silent=True) or {}
    answers = body.get("answers")
    if not isinstance(answers, dict):
        return jsonify({"error": "Missing answers"}), 400

    now = auth_lib.utc_now_iso()
    with db_conn(DB_PATH) as conn:
        migrate(conn)
        existing = fetch_one(conn, "SELECT user_id FROM onboarding_answers WHERE user_id = ?", (user.user_id,))
        if existing:
            conn.execute(
                "UPDATE onboarding_answers SET answers_json = ?, updated_at = ? WHERE user_id = ?",
                (json.dumps(answers, ensure_ascii=False), now, user.user_id),
            )
        else:
            conn.execute(
                "INSERT INTO onboarding_answers(user_id, answers_json, created_at, updated_at) VALUES(?,?,?,?)",
                (user.user_id, json.dumps(answers, ensure_ascii=False), now, now),
            )
    return jsonify({"ok": True})


def get_pairing_for_user(conn, user: auth_lib.AuthedUser) -> list[dict[str, Any]]:
    if user.role == "client":
        rows = conn.execute(
            "SELECT id, client_user_id, trusted_user_id, status FROM pairings WHERE client_user_id = ? AND status = 'accepted'",
            (user.user_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, client_user_id, trusted_user_id, status FROM pairings WHERE trusted_user_id = ? AND status = 'accepted'",
            (user.user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


@app.route("/api/sharing", methods=["GET"])
def api_sharing_get():
    user = auth_required_json()
    with db_conn(DB_PATH) as conn:
        migrate(conn)
        pairings = get_pairing_for_user(conn, user)
        # For MVP, return settings per pairing (or defaults if missing)
        out = []
        for p in pairings:
            row = fetch_one(conn, "SELECT fields_allowed_json, updated_at FROM share_settings WHERE pairing_id = ?", (p["id"],))
            if row:
                allowed = json.loads(row["fields_allowed_json"])
            else:
                allowed = {
                    "share_anxiety_level": True,
                    "share_sleep": True,
                    "share_caffeine": True,
                    "share_heart_rate": False,
                    "share_breathing_rate": False,
                    "share_stress_event": True,
                    "share_context": False,
                    "share_patterns": True,
                    "share_risk_levels": True,
                }
            out.append({"pairing_id": p["id"], "fields_allowed": allowed})
    return jsonify({"ok": True, "settings": out})


@app.route("/api/sharing", methods=["POST"])
def api_sharing_post():
    user = auth_required_json()
    ensure_role(user, "client")
    body = request.get_json(silent=True) or {}
    pairing_id = body.get("pairing_id")
    fields_allowed = body.get("fields_allowed")
    if not isinstance(pairing_id, int) or not isinstance(fields_allowed, dict):
        return jsonify({"error": "Missing pairing_id or fields_allowed"}), 400

    now = auth_lib.utc_now_iso()
    with db_conn(DB_PATH) as conn:
        migrate(conn)
        pairing = fetch_one(
            conn,
            "SELECT id FROM pairings WHERE id = ? AND client_user_id = ? AND status = 'accepted'",
            (pairing_id, user.user_id),
        )
        if not pairing:
            return jsonify({"error": "Pairing not found"}), 404

        existing = fetch_one(conn, "SELECT pairing_id FROM share_settings WHERE pairing_id = ?", (pairing_id,))
        if existing:
            conn.execute(
                "UPDATE share_settings SET fields_allowed_json = ?, updated_at = ? WHERE pairing_id = ?",
                (json.dumps(fields_allowed, ensure_ascii=False), now, pairing_id),
            )
        else:
            conn.execute(
                "INSERT INTO share_settings(pairing_id, fields_allowed_json, updated_at) VALUES(?,?,?)",
                (pairing_id, json.dumps(fields_allowed, ensure_ascii=False), now),
            )
    return jsonify({"ok": True})

@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=True)
