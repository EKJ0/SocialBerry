# Tracker (ML risk models)

Standalone package: ingest check-ins + episodes, train **binary** models for “episode in next 1 hour” and “episode in next 24 hours”, then map predicted probability to **low / medium / high** (not an exact-time forecast).

## Setup

From repo root (`PlantMe` folder):

```bash
python -m pip install -r tracker/requirements.txt
```

Windows PowerShell (same folder):

```powershell
python -m pip install -r tracker\requirements.txt
```

## Browser UI (enter your own numbers)

After models exist (`run_demo` or `train`), start a tiny local page:

```bash
python -m tracker.web
```

Open **http://127.0.0.1:5050** in Chrome, Edge, or Firefox. Fill the form and click **Estimate risk**.

## Quick check (recommended)

Loads sample rows into `tracker/data/tracker.sqlite3`, trains **without** merging extra synthetic data, then prints a sample prediction:

```bash
python -m tracker.run_demo
```

Or:

```bash
python tracker/run_demo.py
```

## Train (other options)

You can also run training directly (works as a module **or** as a script thanks to path bootstrapping):

```bash
python -m tracker.train --synthetic-only
python tracker/train.py --synthetic-only
```

## Add your dataset

Put CSV files in `**tracker/datasets/**` (see `tracker/datasets/README.md` for column names).

Import into SQLite:

```bash
python -m tracker.load_csv --dir tracker/datasets
```

Replace all existing rows:

```bash
python -m tracker.load_csv --dir tracker/datasets --replace
```

## Train from SQLite (after CSV import)

Uses `tracker/data/tracker.sqlite3`. If there are **fewer than 80** check-ins, **synthetic data is merged** automatically (unless `--real-only`).

```bash
python -m tracker.train
python tracker/train.py
```

Train only on DB rows (no synthetic merge — needs enough data):

```bash
python -m tracker.train --real-only
```

## Predict (Python)

```python
from tracker.predict import predict_from_dict

print(predict_from_dict({
    "anxiety_level": 7,
    "sleep_hours": 5.0,
    "caffeine_mg": 200,
    "heart_rate_bpm": 98,
    "breathing_rate_bpm": 22,
    "stress_event": "deadline",
    "context": "work",
    "food_level": 3,
    "hours_since_last_episode": 48,
}))
```

## Data model (SQLite)

- `checkins`: signals at a timestamp (`user_id`, `ts`, …)
- `episodes`: anxiety/panic episodes (`user_id`, `ts`)

Labels for training are derived from timelines: after each check-in, did an episode occur in `(now, now+1h]` and `(now, now+24h]`?

## Outputs

- `tracker/models/model_next_hour.joblib`
- `tracker/models/model_next_day.joblib`
- `tracker/models/train_meta.json`

