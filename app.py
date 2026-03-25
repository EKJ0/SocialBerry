from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any

from flask import (
    Flask,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "plantme.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "replace-this-in-production"

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

TOOLS = [
    {"name": "2-Minute Breathe", "time": "2 min", "tag": "Fast relief", "description": "A simple inhale-hold-exhale pattern to calm mental overload."},
    {"name": "Mind Dump Journal", "time": "5 min", "tag": "Clarity", "description": "Write everything in your head, then sort into now, later, and let go."},
    {"name": "Reset Walk", "time": "10 min", "tag": "Energy", "description": "Step away from your screen and do one short walk without notifications."},
    {"name": "Grounding Scan", "time": "3 min", "tag": "Anxiety", "description": "Notice 5 things you see, 4 you feel, 3 you hear, 2 you smell, 1 you taste."},
]

DEFAULT_EVENTS = [
    {
        "title": "Campus Sunset Walk",
        "category": "Movement",
        "date": "2026-03-27",
        "time": "18:30",
        "location": "Central Park Loop",
        "city": "Dubai",
        "price": 3,
        "spots": 24,
        "lat": 25.2048,
        "lng": 55.2708,
        "description": "A relaxed guided walk to decompress after classes.",
    },
    {
        "title": "Journaling Circle",
        "category": "Reflection",
        "date": "2026-03-28",
        "time": "17:00",
        "location": "Knowledge Village Hub",
        "city": "Dubai",
        "price": 4,
        "spots": 12,
        "lat": 25.1032,
        "lng": 55.1692,
        "description": "Prompt-based journaling for overwhelmed students.",
    },
    {
        "title": "Breath & Reset Workshop",
        "category": "Stress Relief",
        "date": "2026-03-29",
        "time": "11:00",
        "location": "Student Wellness Hub",
        "city": "Dubai",
        "price": 5,
        "spots": 18,
        "lat": 25.1972,
        "lng": 55.2744,
        "description": "Learn calming breathing techniques you can use before exams.",
    },
    {
        "title": "Art Therapy Mini Session",
        "category": "Creativity",
        "date": "2026-03-29",
        "time": "15:00",
        "location": "Student Center Studio",
        "city": "Dubai",
        "price": 5,
        "spots": 10,
        "lat": 25.2285,
        "lng": 55.3273,
        "description": "A guided creative reset session to process stress gently.",
    },
]

HABIT_LIBRARY = [
    "Hydrate",
    "10-minute walk",
    "Breathing reset",
    "Journal entry",
    "Sleep routine",
    "Time outdoors",
    "Study break",
    "Text a friend",
]


@app.before_request
def before_request() -> None:
    g.db = get_db()
    g.user = get_current_user()


@app.teardown_request
def teardown_request(exception: BaseException | None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.context_processor
def inject_globals() -> dict[str, Any]:
    return {"year": datetime.now().year, "current_user": g.get("user"), "habit_library": HABIT_LIBRARY}


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def get_current_user() -> sqlite3.Row | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    return g.db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            flash("Please log in to access your dashboard.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def query_value(sql: str, params: tuple[Any, ...] = ()) -> int:
    row = g.db.execute(sql, params).fetchone()
    return int(row[0]) if row and row[0] is not None else 0


def init_db() -> None:
    with closing(sqlite3.connect(DATABASE)) as db:
        reset_legacy_tables(db)
        db.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                mood TEXT NOT NULL,
                energy INTEGER NOT NULL,
                stress INTEGER NOT NULL,
                sleep INTEGER NOT NULL,
                social_battery INTEGER NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS habit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                habit_name TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                mood_tag TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS support_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                support_type TEXT NOT NULL,
                message TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                location TEXT NOT NULL,
                city TEXT NOT NULL,
                price REAL NOT NULL,
                spots INTEGER NOT NULL,
                lat REAL NOT NULL,
                lng REAL NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS event_bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                event_id INTEGER NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
                UNIQUE(event_id, email)
            );
            """
        )
        db.commit()
        seed_events(db)




def reset_legacy_tables(db: sqlite3.Connection) -> None:
    expected = {
        "checkins": {"user_id", "mood", "energy", "stress", "sleep", "social_battery", "notes", "created_at"},
        "support_requests": {"user_id", "full_name", "email", "support_type", "message", "created_at"},
        "event_bookings": {"user_id", "event_id", "full_name", "email", "created_at"},
        "events": {"title", "category", "date", "time", "location", "city", "price", "spots", "lat", "lng", "description", "created_at"},
    }
    for table_name, required_columns in expected.items():
        exists = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone()
        if not exists:
            continue
        cols = {row[1] for row in db.execute(f"PRAGMA table_info({table_name})").fetchall()}
        if not required_columns.issubset(cols):
            db.execute(f"DROP TABLE IF EXISTS {table_name}")
    db.commit()

def seed_events(db: sqlite3.Connection) -> None:
    existing = db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    if existing:
        return
    now = datetime.now().isoformat(timespec="seconds")
    db.executemany(
        """
        INSERT INTO events (title, category, date, time, location, city, price, spots, lat, lng, description, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item["title"],
                item["category"],
                item["date"],
                item["time"],
                item["location"],
                item["city"],
                item["price"],
                item["spots"],
                item["lat"],
                item["lng"],
                item["description"],
                now,
            )
            for item in DEFAULT_EVENTS
        ],
    )
    db.commit()


def calculate_burnout(checkins: list[sqlite3.Row], habits: list[sqlite3.Row]) -> dict[str, Any]:
    if not checkins:
        return {
            "score": 22,
            "level": "Low",
            "label": "Seedling",
            "garden_stage": "Seedling",
            "completion": 18,
            "advice": "Start with one honest check-in and one tiny habit today.",
            "recommendations": [
                "Try the 2-minute breathing reset.",
                "Log your first mood check-in.",
                "Pick one habit that feels easy, not perfect.",
            ],
        }

    recent = checkins[:7]
    avg_stress = sum(row["stress"] for row in recent) / len(recent)
    avg_sleep = sum(row["sleep"] for row in recent) / len(recent)
    avg_energy = sum(row["energy"] for row in recent) / len(recent)
    avg_social = sum(row["social_battery"] for row in recent) / len(recent)
    habit_count = len([row for row in habits if row["completed"]])
    habit_bonus = min(habit_count * 2.5, 20)

    score = 50
    score += (avg_stress - 5) * 7
    score += (5 - avg_sleep) * 5
    score += (5 - avg_energy) * 6
    score += (5 - avg_social) * 3
    score -= habit_bonus

    latest_mood = recent[0]["mood"]
    if latest_mood == "burned_out":
        score += 10
    elif latest_mood == "stressed":
        score += 6
    elif latest_mood == "great":
        score -= 4

    score = max(0, min(100, round(score)))

    if score >= 75:
        level = "High"
        garden_stage = "Dormant"
        completion = 24
        advice = "Your recent pattern suggests strong burnout risk. Reduce load, prioritize rest, and consider human support."
        recommendations = [
            "Book a support conversation this week.",
            "Choose one task to postpone or delegate today.",
            "Use the grounding scan before studying again.",
        ]
    elif score >= 50:
        level = "Moderate"
        garden_stage = "Sprouting"
        completion = 55
        advice = "You are carrying more stress than your current routines are absorbing. A reset plan would help."
        recommendations = [
            "Complete two small habits today.",
            "Take a 10-minute reset walk.",
            "Journal what is mentally loud right now.",
        ]
    else:
        level = "Low"
        garden_stage = "Blooming"
        completion = 88
        advice = "Your recent signals look relatively stable. Protect what is working and keep your routines gentle."
        recommendations = [
            "Keep your current habits going.",
            "Do one gratitude note tonight.",
            "Schedule one social or outdoor moment this week.",
        ]

    return {
        "score": score,
        "level": level,
        "label": f"{level} Risk",
        "garden_stage": garden_stage,
        "completion": completion,
        "advice": advice,
        "recommendations": recommendations,
    }


def build_summary(checkins: list[sqlite3.Row], habits: list[sqlite3.Row]) -> dict[str, Any]:
    if not checkins:
        return {
            "avg_stress": 0,
            "avg_sleep": 0,
            "avg_energy": 0,
            "avg_social": 0,
            "habit_count": len(habits),
            "checkin_count": 0,
        }

    total = len(checkins)
    return {
        "avg_stress": round(sum(row["stress"] for row in checkins) / total, 1),
        "avg_sleep": round(sum(row["sleep"] for row in checkins) / total, 1),
        "avg_energy": round(sum(row["energy"] for row in checkins) / total, 1),
        "avg_social": round(sum(row["social_battery"] for row in checkins) / total, 1),
        "habit_count": len(habits),
        "checkin_count": total,
    }


def chart_payload(checkins: list[sqlite3.Row]) -> dict[str, list[Any]]:
    ordered = list(reversed(checkins[:7]))
    return {
        "labels": [row["created_at"][5:10] for row in ordered],
        "stress": [row["stress"] for row in ordered],
        "energy": [row["energy"] for row in ordered],
        "sleep": [row["sleep"] for row in ordered],
    }


def available_spots(event_row: sqlite3.Row) -> int:
    booked = query_value("SELECT COUNT(*) FROM event_bookings WHERE event_id = ?", (event_row["id"],))
    return max(0, event_row["spots"] - booked)


@app.route("/")
def home() -> str:
    events = g.db.execute("SELECT * FROM events ORDER BY date, time LIMIT 4").fetchall()
    event_cards = [dict(event, remaining_spots=available_spots(event)) for event in events]
    stats = {
        "checkins": query_value("SELECT COUNT(*) FROM checkins"),
        "support_requests": query_value("SELECT COUNT(*) FROM support_requests"),
        "event_bookings": query_value("SELECT COUNT(*) FROM event_bookings"),
        "users": query_value("SELECT COUNT(*) FROM users"),
    }
    return render_template(
        "home.html",
        stats=stats,
        support_options=SUPPORT_OPTIONS,
        events=event_cards,
        tools=TOOLS,
    )


@app.route("/register", methods=["GET", "POST"])
def register() -> str:
    if g.user is not None:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not full_name or not email or not password:
            flash("Please complete all fields.", "error")
            return redirect(url_for("register"))
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return redirect(url_for("register"))

        try:
            g.db.execute(
                "INSERT INTO users (full_name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (full_name, email, generate_password_hash(password), datetime.now().isoformat(timespec="seconds")),
            )
            g.db.commit()
        except sqlite3.IntegrityError:
            flash("That email is already registered.", "error")
            return redirect(url_for("register"))

        user = g.db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        session["user_id"] = user["id"]
        flash("Welcome to PlantMe. Your account is ready.", "success")
        return redirect(url_for("dashboard"))

    return render_template("auth.html", mode="register")


@app.route("/login", methods=["GET", "POST"])
def login() -> str:
    if g.user is not None:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = g.db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Incorrect email or password.", "error")
            return redirect(url_for("login"))

        session.clear()
        session["user_id"] = user["id"]
        flash("Welcome back.", "success")
        return redirect(url_for("dashboard"))

    return render_template("auth.html", mode="login")


@app.route("/logout")
def logout() -> str:
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard() -> str:
    if request.method == "POST":
        form = request.form
        action = form.get("action")

        if action == "checkin":
            g.db.execute(
                """
                INSERT INTO checkins (user_id, mood, energy, stress, sleep, social_battery, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    g.user["id"],
                    form.get("mood", "okay"),
                    int(form.get("energy", 5)),
                    int(form.get("stress", 5)),
                    int(form.get("sleep", 5)),
                    int(form.get("social_battery", 5)),
                    form.get("notes", "").strip(),
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            g.db.commit()
            flash("Check-in saved.", "success")
            return redirect(url_for("dashboard"))

        if action == "habit":
            habit_name = form.get("habit_name", "").strip()
            if habit_name:
                g.db.execute(
                    "INSERT INTO habit_logs (user_id, habit_name, completed, created_at) VALUES (?, ?, 1, ?)",
                    (g.user["id"], habit_name, datetime.now().isoformat(timespec="seconds")),
                )
                g.db.commit()
                flash(f"Habit logged: {habit_name}.", "success")
            else:
                flash("Choose a habit to log.", "error")
            return redirect(url_for("dashboard"))

        if action == "journal":
            title = form.get("title", "").strip()
            content = form.get("content", "").strip()
            mood_tag = form.get("mood_tag", "").strip()
            if title and content:
                g.db.execute(
                    "INSERT INTO journal_entries (user_id, title, content, mood_tag, created_at) VALUES (?, ?, ?, ?, ?)",
                    (g.user["id"], title, content, mood_tag, datetime.now().isoformat(timespec="seconds")),
                )
                g.db.commit()
                flash("Journal entry saved.", "success")
            else:
                flash("Journal title and entry are required.", "error")
            return redirect(url_for("dashboard"))

    checkins = g.db.execute(
        "SELECT * FROM checkins WHERE user_id = ? ORDER BY id DESC LIMIT 8",
        (g.user["id"],),
    ).fetchall()
    habits = g.db.execute(
        "SELECT * FROM habit_logs WHERE user_id = ? ORDER BY id DESC LIMIT 12",
        (g.user["id"],),
    ).fetchall()
    journals = g.db.execute(
        "SELECT * FROM journal_entries WHERE user_id = ? ORDER BY id DESC LIMIT 4",
        (g.user["id"],),
    ).fetchall()

    summary = build_summary(checkins, habits)
    burnout = calculate_burnout(checkins, habits)

    return render_template(
        "dashboard.html",
        checkins=checkins,
        habits=habits,
        journals=journals,
        summary=summary,
        burnout=burnout,
        chart_data=chart_payload(checkins),
        tools=TOOLS,
    )


@app.route("/support", methods=["GET", "POST"])
@login_required
def support() -> str:
    if request.method == "POST":
        support_type = request.form.get("support_type", "Support Conversation")
        message = request.form.get("message", "").strip()
        g.db.execute(
            """
            INSERT INTO support_requests (user_id, full_name, email, support_type, message, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                g.user["id"],
                g.user["full_name"],
                g.user["email"],
                support_type,
                message,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        g.db.commit()
        flash("Support request received.", "success")
        return redirect(url_for("support"))

    requests_data = g.db.execute(
        "SELECT * FROM support_requests WHERE user_id = ? ORDER BY id DESC LIMIT 6",
        (g.user["id"],),
    ).fetchall()
    return render_template("support.html", support_options=SUPPORT_OPTIONS, requests_data=requests_data)


@app.route("/events", methods=["GET", "POST"])
def events() -> str:
    if request.method == "POST":
        if g.user is None:
            flash("Please log in to book an event.", "error")
            return redirect(url_for("login"))

        event_id = int(request.form.get("event_id", 0))
        event_row = g.db.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        if event_row is None:
            flash("Event not found.", "error")
            return redirect(url_for("events"))
        if available_spots(event_row) <= 0:
            flash("That event is fully booked.", "error")
            return redirect(url_for("events"))

        try:
            g.db.execute(
                "INSERT INTO event_bookings (user_id, event_id, full_name, email, created_at) VALUES (?, ?, ?, ?, ?)",
                (g.user["id"], event_id, g.user["full_name"], g.user["email"], datetime.now().isoformat(timespec="seconds")),
            )
            g.db.commit()
            flash("Your event spot is reserved.", "success")
        except sqlite3.IntegrityError:
            flash("You already booked this event.", "error")
        return redirect(url_for("events"))

    events_data = g.db.execute("SELECT * FROM events ORDER BY date, time").fetchall()
    event_cards = [dict(event, remaining_spots=available_spots(event)) for event in events_data]
    bookings = []
    if g.user is not None:
        bookings = g.db.execute(
            """
            SELECT eb.created_at, e.title, e.date, e.time, e.location
            FROM event_bookings eb
            JOIN events e ON e.id = eb.event_id
            WHERE eb.user_id = ?
            ORDER BY eb.id DESC LIMIT 8
            """,
            (g.user["id"],),
        ).fetchall()
    return render_template("events.html", events=event_cards, bookings=bookings)


@app.route("/api/events")
def events_api():
    events_data = g.db.execute("SELECT * FROM events ORDER BY date, time").fetchall()
    features = []
    for event in events_data:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [event["lng"], event["lat"]]},
                "properties": {
                    "id": event["id"],
                    "title": event["title"],
                    "category": event["category"],
                    "date": event["date"],
                    "time": event["time"],
                    "location": event["location"],
                    "city": event["city"],
                    "price": event["price"],
                },
            }
        )
    return jsonify({"type": "FeatureCollection", "features": features})


@app.route("/pricing")
def pricing() -> str:
    return render_template("pricing.html")


@app.route("/about")
def about() -> str:
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact() -> str:
    if request.method == "POST":
        flash("Thanks for reaching out. Wire this form to a real inbox next.", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html")


init_db()

if __name__ == "__main__":
    app.run(debug=True)
