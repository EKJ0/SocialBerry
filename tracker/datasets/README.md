# Put your dataset here

Drop **CSV** files in this folder (or any folder you pass to the loader).

## Option A — two files (recommended)

### `checkins.csv`

Each row is one signal snapshot per user at a point in time.


| Column (use one of the aliases)                | Required | Notes                                |
| ---------------------------------------------- | -------- | ------------------------------------ |
| `user_id` (or `user`, `subject_id`)            | yes      | Stable ID per person                 |
| `ts` (or `timestamp`, `datetime`, `time`)      | yes      | ISO-8601, e.g. `2025-03-01T14:30:00` |
| `anxiety_level` (or `anxiety`, `stress_level`) | yes      | 0–10 scale                           |
| `sleep_hours` (or `sleep`)                     | no       | hours                                |
| `caffeine_mg` (or `caffeine`)                  | no       | mg                                   |
| `heart_rate_bpm` (or `hr`, `heart_rate`)       | no       | bpm                                  |
| `breathing_rate_bpm` (or `br`, `resp_rate`)    | no       | breaths/min                          |
| `stress_event` (or `stress_type`)              | no       | e.g. `deadline`, `commute`, or empty |
| `context` (or `location`, `place`)             | no       | e.g. `home`, `work`, `commute`       |
| `food_level` (or `food`)                       | no       | 0–10                                 |


### `episodes.csv`

Each row is one **episode** (panic/anxiety spike you want the model to anticipate).


| Column                            | Required                   |
| --------------------------------- | -------------------------- |
| `user_id`                         | yes (same IDs as checkins) |
| `ts` (or `timestamp`, `datetime`) | yes                        |


## Option B — one file

If you only have checkins and **no separate episode list**, put `checkins.csv` here and omit `episodes.csv`. Training will still run, but labels (“episode in next hour/day”) will be mostly zeros unless you add episodes later.

## After you add files

From the **PlantMe** repo root:

```bash
python -m tracker.load_csv --dir tracker/datasets
```

Then train on real data (no synthetic merge if you have enough rows, or use `--real-only` when ready):

```bash
python -m tracker.train --real-only
python -m tracker.predict
```

**First-time sanity check** (no CSV needed): `python -m tracker.run_demo`

If you have fewer than ~80 check-ins, the trainer will still **merge synthetic data** unless you pass `--real-only` (then you may get a weak or constant model).