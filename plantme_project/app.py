from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from flask import Flask, abort, render_template

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'

app = Flask(__name__)


def load_json(filename: str) -> Any:
    path = DATA_DIR / filename
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


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
        return render_template('dashboard_client.html', client=data['client'], therapist=data['therapist'])
    if role == 'therapist':
        return render_template('dashboard_therapist.html', therapist=data['therapist'], clients=data['clients'])
    abort(404)


@app.route('/tasks/<role>')
def tasks(role: str):
    data = load_json('seed_data.json')
    if role == 'client':
        return render_template('tasks_client.html', client=data['client'])
    if role == 'therapist':
        return render_template('tasks_therapist.html', therapist=data['therapist'], clients=data['clients'])
    abort(404)


@app.route('/garden')
def garden():
    data = load_json('seed_data.json')
    return render_template('garden.html', garden=data['garden'], client=data['client'])


@app.route('/messages')
def messages():
    data = load_json('seed_data.json')
    return render_template('messages.html', messages=data['messages'], therapist=data['therapist'], client=data['client'])


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=True)
