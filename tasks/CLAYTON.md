# 📊 Clayton — Database Schema + Analysis Engine

Clayton owned the database and all the statistics. The correlation engine is what makes the app genuinely useful rather than just a voice-powered notepad.

**Branch:** `clayton/db-analysis`

---

## What Was Built

### Database Schema (`db/init.sql`)
All tables implemented and deployed via Docker:

- **`users`** — `id` (UUID primary key), `created_at`. Demo user `00000000-0000-0000-0000-000000000001` seeded on startup.
- **`entries`** — full log entry with `symptoms` (array), `severity` (1–10 check constraint), `potential_triggers` (array), `mood`, `body_location` (array), `time_context`, `notes`, `logged_at`.
- **`correlations`** — statistical relationships between symptoms and triggers.
- **`insights_cache`** — pre-computed insights as JSONB, with `entry_count_at_computation` to detect stale cache.
- **`trigger_taxonomy`** — maps raw trigger strings to canonical root-cause categories per user. Unique constraint on `(user_id, raw_trigger)` prevents duplicate mappings.

Indexes on `user_id` and `logged_at` on `entries`. GIN indexes on `symptoms` and `potential_triggers` for fast array lookups. Indexes on `trigger_taxonomy` for raw trigger and root cause lookups.

### SQLAlchemy Models (`backend/models/models.py`)
All tables modeled: `User`, `Entry`, `Correlation`, `InsightsCache`, `TriggerTaxonomy`.

### Analysis Engine (`backend/services/analysis.py`)
All four analysis functions implemented:

1. **`compute_trigger_correlation(entries)`** — counts how often each trigger appeared within 24 hours preceding a symptom. Returns `[{name, value}]` for Max's bar chart. Requires ≥ 5 entries and ≥ 3 co-occurrences per trigger.

2. **`compute_temporal_patterns(entries)`** — groups symptoms by day-of-week and `time_context`. Returns `[{symptom, peak_day, peak_time, frequency}]` for symptoms with ≥ 4 entries and a clear clustering pattern.

3. **`compute_severity_trends(entries)`** — computes daily average severity over the last 7 days. Returns `[{date, severity}]` for Max's line chart.

4. **`compute_symptom_frequency(entries)`** — counts total occurrences per symptom. Returns `[{name, value}]` for Max's pie/donut chart.

5. **`compute_all_stats(user_id, db)`** — master function combining all four into one JSON blob. Returns `"Insufficient data"` message for < 5 entries. All functions handle empty/small datasets gracefully.

### API Routes
- `GET /api/stats/{user_id}` — returns severity trends and trigger correlations formatted for Recharts
- `GET /api/history/{user_id}` — returns all log entries, most recent first, serialized for the frontend
- `PUT /api/entries/{entry_id}` — updates symptoms, triggers, notes, and severity on an existing entry

### Seed Script (`backend/seed.py`)
Populated 30 days of fake entries for the demo user with baked-in patterns (caffeine → headache, stress → stomach ache, poor sleep → fatigue, alcohol → headache).

---

## Key Files
- `db/init.sql` — PostgreSQL schema and demo user seed
- `backend/models/models.py` — SQLAlchemy ORM models
- `backend/database.py` — database engine and session factory
- `backend/services/analysis.py` — analysis engine (all 4 functions)
- `backend/seed.py` — demo data seed script
