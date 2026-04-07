"""
Simple browser UI for the tracker: enter signals, see risk output.

From repo root:
  python -m tracker.web

Then open http://127.0.0.1:5050 in Chrome / Edge / Firefox.

Requires trained models (run: python -m tracker.run_demo).
"""

from __future__ import annotations

import html
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from flask import Flask, redirect, request, url_for

from tracker.predict import models_ready, predict_from_dict

app = Flask(__name__)


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PlantMe Tracker – check-in</title>
  <style>
    :root {{ font-family: system-ui, sans-serif; background: #f4f7f4; color: #1a2e1a; }}
    body {{ max-width: 520px; margin: 2rem auto; padding: 0 1rem; }}
    h1 {{ font-size: 1.35rem; }}
    .card {{ background: #fff; border-radius: 12px; padding: 1.25rem; box-shadow: 0 4px 20px rgba(0,0,0,.06); margin-bottom: 1rem; }}
    label {{ display: block; font-weight: 600; margin: 0.75rem 0 0.25rem; font-size: 0.9rem; }}
    input, select {{ width: 100%; padding: 0.5rem 0.6rem; border: 1px solid #c8d9c8; border-radius: 8px; font-size: 1rem; box-sizing: border-box; }}
    button {{ margin-top: 1rem; background: #3d8b40; color: #fff; border: none; padding: 0.65rem 1.2rem; border-radius: 8px; font-weight: 700; cursor: pointer; font-size: 1rem; }}
    button:hover {{ background: #2f6d32; }}
    .warn {{ background: #fff8e6; border: 1px solid #e6c200; padding: 0.75rem; border-radius: 8px; font-size: 0.9rem; }}
    .out {{ background: #eef6ee; border: 1px solid #a3c9a5; padding: 1rem; border-radius: 8px; }}
    .out h2 {{ margin: 0 0 0.5rem; font-size: 1rem; }}
    .level {{ font-size: 1.25rem; font-weight: 800; text-transform: capitalize; }}
    .muted {{ color: #5a6b5a; font-size: 0.85rem; margin-top: 0.5rem; }}
    a {{ color: #2f6d32; }}
  </style>
</head>
<body>
  <h1>Tracker check-in</h1>
  <p class="muted">Not medical advice. Not an exact-time prediction.</p>

  {warning}

  <div class="card">
    <form method="post" action="{predict_url}">
      <label for="anxiety_level">Anxiety level (0–10) *</label>
      <input id="anxiety_level" name="anxiety_level" type="number" min="0" max="10" step="1" value="{anxiety_level}" required>

      <label for="sleep_hours">Sleep (hours)</label>
      <input id="sleep_hours" name="sleep_hours" type="number" min="0" max="24" step="0.1" value="{sleep_hours}">

      <label for="caffeine_mg">Caffeine (mg)</label>
      <input id="caffeine_mg" name="caffeine_mg" type="number" min="0" step="10" value="{caffeine_mg}">

      <label for="heart_rate_bpm">Heart rate (bpm)</label>
      <input id="heart_rate_bpm" name="heart_rate_bpm" type="number" min="0" max="240" value="{heart_rate_bpm}">

      <label for="breathing_rate_bpm">Breathing rate (breaths/min)</label>
      <input id="breathing_rate_bpm" name="breathing_rate_bpm" type="number" min="0" max="60" value="{breathing_rate_bpm}">

      <label for="food_level">Food level (0 empty – 10 well fed)</label>
      <input id="food_level" name="food_level" type="number" min="0" max="10" step="1" value="{food_level}">

      <label for="hours_since_last_episode">Hours since last episode (optional)</label>
      <input id="hours_since_last_episode" name="hours_since_last_episode" type="number" min="0" step="1" value="{hours_since_last_episode}">

      <label for="stress_event">Stress event</label>
      <select id="stress_event" name="stress_event">
        {stress_options}
      </select>

      <label for="context">Context</label>
      <select id="context" name="context">
        {context_options}
      </select>

      <button type="submit">Estimate risk</button>
    </form>
  </div>

  {result}
</body>
</html>
"""


def _opt(name: str, value: str, current: str) -> str:
    sel = " selected" if current == value else ""
    return f'<option value="{html.escape(value)}"{sel}>{html.escape(name)}</option>'


def _select_group(options: list[tuple[str, str]], current: str) -> str:
    return "\n        ".join(_opt(label, val, current) for label, val in options)


@app.get("/")
def index():
    warning = ""
    if not models_ready():
        warning = (
            '<div class="warn"><strong>No models yet.</strong> In PowerShell, from the PlantMe folder, run: '
            "<code>python -m tracker.run_demo</code> then refresh this page.</div>"
        )

    stress_opts = [
        ("(none)", ""),
        ("Conflict", "conflict"),
        ("Deadline", "deadline"),
        ("Health worry", "health"),
        ("Social", "social"),
        ("Commute", "commute"),
        ("Other", "other"),
    ]
    ctx_opts = [
        ("(none)", ""),
        ("Home", "home"),
        ("Work", "work"),
        ("Commute", "commute"),
        ("Public", "public"),
    ]

    body = PAGE.format(
        warning=warning,
        predict_url=html.escape(url_for("predict")),
        anxiety_level="5",
        sleep_hours="",
        caffeine_mg="",
        heart_rate_bpm="",
        breathing_rate_bpm="",
        food_level="",
        hours_since_last_episode="",
        stress_options=_select_group(stress_opts, ""),
        context_options=_select_group(ctx_opts, ""),
        result="",
    )
    return body


def _float_or_none(key: str) -> float | None:
    raw = (request.form.get(key) or "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


@app.post("/predict")
def predict():
    if not models_ready():
        return redirect(url_for("index"))

    stress = (request.form.get("stress_event") or "").strip()
    context = (request.form.get("context") or "").strip()

    payload = {
        "anxiety_level": float(request.form.get("anxiety_level") or 0),
        "sleep_hours": _float_or_none("sleep_hours"),
        "caffeine_mg": _float_or_none("caffeine_mg"),
        "heart_rate_bpm": _float_or_none("heart_rate_bpm"),
        "breathing_rate_bpm": _float_or_none("breathing_rate_bpm"),
        "food_level": _float_or_none("food_level"),
        "hours_since_last_episode": _float_or_none("hours_since_last_episode"),
        "stress_event": stress,
        "context": context,
    }

    try:
        out = predict_from_dict(payload)
    except Exception as e:
        err = html.escape(str(e))
        result_html = f'<div class="warn"><strong>Input error:</strong> {err}</div>'
        return _render_form_with_result(request.form, result_html)

    h = out["risk_next_hour"]
    d = out["risk_next_day"]
    result_html = f"""
  <div class="card out">
    <h2>Next hour</h2>
    <div class="level">{html.escape(h["level"])}</div>
    <div class="muted">Approx. chance of an episode: {h["probability_episode"]}</div>
    <div class="muted">{html.escape(h["note"])}</div>
    <h2 style="margin-top:1rem">Next day</h2>
    <div class="level">{html.escape(d["level"])}</div>
    <div class="muted">Approx. chance of an episode: {d["probability_episode"]}</div>
    <div class="muted">{html.escape(d["note"])}</div>
  </div>
"""
    return _render_form_with_result(request.form, result_html)


def _render_form_with_result(form_data, result_html: str) -> str:
    warning = ""
    if not models_ready():
        warning = '<div class="warn">Train models first: <code>python -m tracker.run_demo</code></div>'

    stress_opts = [
        ("(none)", ""),
        ("Conflict", "conflict"),
        ("Deadline", "deadline"),
        ("Health worry", "health"),
        ("Social", "social"),
        ("Commute", "commute"),
        ("Other", "other"),
    ]
    ctx_opts = [
        ("(none)", ""),
        ("Home", "home"),
        ("Work", "work"),
        ("Commute", "commute"),
        ("Public", "public"),
    ]

    def gv(key: str, default: str = "") -> str:
        return html.escape((form_data.get(key) or default) if hasattr(form_data, "get") else default)

    # form_data may be ImmutableMultiDict
    stress_cur = (form_data.get("stress_event") or "").strip()
    ctx_cur = (form_data.get("context") or "").strip()

    body = PAGE.format(
        warning=warning,
        predict_url=html.escape(url_for("predict")),
        anxiety_level=gv("anxiety_level", "5"),
        sleep_hours=gv("sleep_hours"),
        caffeine_mg=gv("caffeine_mg"),
        heart_rate_bpm=gv("heart_rate_bpm"),
        breathing_rate_bpm=gv("breathing_rate_bpm"),
        food_level=gv("food_level"),
        hours_since_last_episode=gv("hours_since_last_episode"),
        stress_options=_select_group(stress_opts, stress_cur),
        context_options=_select_group(ctx_opts, ctx_cur),
        result=result_html,
    )
    return body


def main() -> None:
    print("Open in your browser: http://127.0.0.1:5050")
    print("Press Ctrl+C to stop.")
    app.run(host="127.0.0.1", port=5050, debug=False)


if __name__ == "__main__":
    main()
