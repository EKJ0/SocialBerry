from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, flash, g, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "plantme.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "plantme-demo-secret-key"


MOOD_MAP = {
    "great": {"label": "Thriving", "advice": "Keep your momentum going with a short gratitude note and a light walk."},
    "okay": {"label": "Stable", "advice": "A small reset can help today: hydrate, take a breath break, and avoid doom-scrolling."},
    "stressed": {"label": "At Risk", "advice": "You look overloaded. Try a 2-minute grounding exercise and reduce one non-essential task today."},
    "burned_out": {"label": "High Risk", "advice": "Your pattern suggests burnout risk. Reach out for human support and prioritize rest and a lighter schedule."},
}

SUPPORT_OPTIONS = [
    {
        "type": "Support Conversation",
        "provider": "Psychology Trainee / Mentor",
        "price": "€12",
        "duration": "30 min",
        "description": "Low-pressure guided conversation for stress, overwhelm, loneliness, and study-life balance.",
    },
    {
        "type": "Counseling Session",
        "provider": "Licensed Counselor",
        "price": "€29",
        "duration": "45 min",
        "description": "Professional support for anxiety, burnout signals, and emotional challenges that need deeper guidance.",
    },
    {
        "type": "Focus Reset",
        "provider": "Wellness Coach",
        "price": "€15",
        "duration": "25 min",
        "description": "Short, practical support session to rebuild routines, boundaries, and calm during a heavy week.",
    },
]

EVENTS = [
    {"title": "Campus Sunset Walk", "category": "Movement", "date": "Thu, 18:30", "location": "Central Park Loop", "price": "€3", "spots": 24},
    {"title": "Journaling Circle", "category": "Reflection", "date": "Fri, 17:00", "location": "Library Studio", "price": "€4", "spots": 12},
    {"title": "Breath & Reset Workshop", "category": "Stress Relief", "date": "Sat, 11:00", "location": "Wellness Hub", "price": "€5", "spots": 18},
    {"title": "Art Therapy Mini Session", "category": "Creativity", "date": "Sat, 15:00", "location": "Student Center", "price": "€5", "spots": 10},
]

TOOLS = [
    {"name": "2-Minute Breathe", "time": "2 min", "tag": "Fast relief", "description": "A simple inhale-hold-exhale pattern to calm mental overload."},
    {"name": "Mind Dump Journal", "time": "5 min", "tag": "Clarity", "description": "Write everything in your head, then sort into now, later, and let go."},
    {"name": "Reset Walk", "time": "10 min", "tag": "Energy", "description": "Step away from your screen and do one short walk without notifications."},
    {"name": "Grounding Scan", "time": "3 min", "tag": "Anxiety", "description": "Notice 5 things you see, 4 you feel, 3 you hear, 2 you smell, 1 you taste."},
]


@app.before_request
def before_request() -> None:
    g.db = get_db()


@app.teardown_request
def teardown_request(exception: BaseException | None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(sqlite3.connect(DATABASE)) as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                mood TEXT NOT NULL,
                energy INTEGER NOT NULL,
                stress INTEGER NOT NULL,
                sleep INTEGER NOT NULL,
                social_battery INTEGER NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS support_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                support_type TEXT NOT NULL,
                message TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS event_bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                event_title TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        db.commit()


@app.context_processor
def inject_now() -> dict[str, Any]:
    return {"year": datetime.now().year}


@app.route("/")
def home() -> str:
    stats = {
        "checkins": query_value("SELECT COUNT(*) FROM checkins"),
        "support_requests": query_value("SELECT COUNT(*) FROM support_requests"),
        "event_bookings": query_value("SELECT COUNT(*) FROM event_bookings"),
    }
    latest_checkin = g.db.execute(
        "SELECT * FROM checkins ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return render_template(
        "home.html",
        stats=stats,
        latest_checkin=latest_checkin,
        support_options=SUPPORT_OPTIONS,
        events=EVENTS,
        tools=TOOLS,
    )


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard() -> str:
    if request.method == "POST":
        form = request.form
        name = form.get("name", "Student").strip() or "Student"
        mood = form.get("mood", "okay")
        energy = int(form.get("energy", 5))
        stress = int(form.get("stress", 5))
        sleep = int(form.get("sleep", 5))
        social_battery = int(form.get("social_battery", 5))
        notes = form.get("notes", "").strip()

        g.db.execute(
            """
            INSERT INTO checkins (name, mood, energy, stress, sleep, social_battery, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, mood, energy, stress, sleep, social_battery, notes, datetime.now().isoformat(timespec="seconds")),
        )
        g.db.commit()
        flash("Check-in saved. Your dashboard has been updated.", "success")
        return redirect(url_for("dashboard"))

    checkins = g.db.execute(
        "SELECT * FROM checkins ORDER BY id DESC LIMIT 8"
    ).fetchall()

    summary = build_summary(checkins)
    latest = checkins[0] if checkins else None
    burnout_status = MOOD_MAP.get(latest["mood"], MOOD_MAP["okay"]) if latest else MOOD_MAP["okay"]

    return render_template(
        "dashboard.html",
        checkins=checkins,
        latest=latest,
        burnout_status=burnout_status,
        summary=summary,
        tools=TOOLS,
    )


@app.route("/support", methods=["GET", "POST"])
def support() -> str:
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        support_type = request.form.get("support_type", "Support Conversation")
        message = request.form.get("message", "").strip()

        if not full_name or not email:
            flash("Please provide your name and email.", "error")
            return redirect(url_for("support"))

        g.db.execute(
            """
            INSERT INTO support_requests (full_name, email, support_type, message, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (full_name, email, support_type, message, datetime.now().isoformat(timespec="seconds")),
        )
        g.db.commit()
        flash("Support request received. A confirmation email would normally be sent in production.", "success")
        return redirect(url_for("support"))

    requests_data = g.db.execute(
        "SELECT * FROM support_requests ORDER BY id DESC LIMIT 6"
    ).fetchall()
    return render_template("support.html", support_options=SUPPORT_OPTIONS, requests_data=requests_data)


@app.route("/events", methods=["GET", "POST"])
def events() -> str:
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        event_title = request.form.get("event_title", "").strip()

        if not full_name or not email or not event_title:
            flash("Please fill in all event booking fields.", "error")
            return redirect(url_for("events"))

        g.db.execute(
            """
            INSERT INTO event_bookings (full_name, email, event_title, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (full_name, email, event_title, datetime.now().isoformat(timespec="seconds")),
        )
        g.db.commit()
        flash("Your event spot is reserved.", "success")
        return redirect(url_for("events"))

    bookings = g.db.execute(
        "SELECT * FROM event_bookings ORDER BY id DESC LIMIT 8"
    ).fetchall()
    return render_template("events.html", events=EVENTS, bookings=bookings)


@app.route("/pricing")
def pricing() -> str:
    return render_template("pricing.html")


@app.route("/about")
def about() -> str:
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact() -> str:
    if request.method == "POST":
        flash("Thanks for reaching out. In a production version, this would route to the team inbox.", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html")



def query_value(sql: str) -> int:
    row = g.db.execute(sql).fetchone()
    return int(row[0]) if row else 0



def build_summary(checkins: list[sqlite3.Row]) -> dict[str, Any]:
    if not checkins:
        return {
            "avg_stress": 0,
            "avg_sleep": 0,
            "avg_energy": 0,
            "garden_stage": "Seedling",
            "completion": 8,
        }

    total = len(checkins)
    avg_stress = round(sum(row["stress"] for row in checkins) / total, 1)
    avg_sleep = round(sum(row["sleep"] for row in checkins) / total, 1)
    avg_energy = round(sum(row["energy"] for row in checkins) / total, 1)

    score = avg_energy + avg_sleep - (avg_stress * 0.7)
    if score >= 8:
        garden_stage = "Blooming"
        completion = 92
    elif score >= 5:
        garden_stage = "Growing"
        completion = 68
    else:
        garden_stage = "Seedling"
        completion = 38

    return {
        "avg_stress": avg_stress,
        "avg_sleep": avg_sleep,
        "avg_energy": avg_energy,
        "garden_stage": garden_stage,
        "completion": completion,
    }


init_db()

if __name__ == "__main__":
    app.run(debug=True)
