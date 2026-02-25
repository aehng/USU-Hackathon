# 📊 Clayton — Database Schema + Analysis Engine

You own the database and all the statistics. Your correlation engine is what makes the app genuinely useful rather than just a voice-powered notepad. Your output feeds directly into Noah's LLM insight prompt.

**Branch:** `clayton/db-analysis`

---

## Phase 1 — Setup (Fri 5:00–6:00pm)
- [ ] Clone repo, create your branch
- [ ] Install a database viewer — **DBeaver** (free) or **TablePlus** — you'll want to inspect tables and run raw queries visually
- [ ] Confirm Docker Compose is running and Postgres is accessible
- [ ] Connect your DB viewer to `localhost:5432`, database=`healthtracker`
- [ ] Confirm you can connect (DB will be empty until you run your schema)

---

## Phase 2 — Database Schema (Fri 5:30–6:30pm)

Write `db/init.sql`. Docker will run this automatically on first start.

⚠️ **SCHEMA IS LOCKED.** All tables must be correct before first `docker-compose up`. If bugs are found, you must manually `ALTER TABLE` or reset the DB and re-seed (risky mid-demo).

- [ ] **users table** — `id` (UUID, primary key), `created_at`
- [ ] **entries table** — `id`, `user_id` (foreign key), `raw_transcript`, `symptoms` (array), `severity` (integer 1–10), `potential_triggers` (array), `mood`, `body_location` (array), `time_context`, `notes`, `logged_at` (timestamp)
- [ ] **correlations table** — `id`, `user_id`, `symptom`, `trigger`, `correlation_score` (float), `sample_size` (integer), `computed_at`
- [ ] **insights_cache table** — `id`, `user_id`, `insights_json` (jsonb), `created_at` (timestamp), `entry_count_at_computation` (int)
  - Stores pre-computed insights; Noah writes to this asynchronously
  - Use `entry_count_at_computation` to detect stale cache (don't overwrite if new count < cached count)
- [ ] Add indexes on `user_id` and `logged_at` on the entries table — queries will filter by these constantly
- [ ] Add GIN indexes on the `symptoms` and `potential_triggers` array columns — needed for fast array lookups
- [ ] Insert a hardcoded demo user with a known UUID so everyone can test without auth (`00000000-0000-0000-0000-000000000001`)
- [ ] Share the schema with Noah by 6:30pm so he can write his models
- [ ] **Document this schema in README.md** so the team knows about insights_cache before Noah codes

---

## Phase 3 — SQLAlchemy Models (Fri 6:30–7:30pm)
- [ ] Create `backend/models/` directory with model files for each table
- [ ] Create `backend/database.py` — database engine, session factory, base class
- [ ] Write a quick test: insert one dummy entry programmatically and read it back
- [ ] Make sure Noah can import and use your models in his route handlers

---

## Phase 4 — Analysis Engine (Fri 7:00–11:00pm) ⭐ Your main contribution

Build `backend/services/analysis.py`. This is where your math skills matter.

⚠️ **All functions must handle the minimum-data edge case gracefully:**
- If `entries < 1`: return empty dict `{}`
- If `entries < 5`: return dict with message: `{"message": "Insufficient data", "total_entries": N}`
- Never attempt division, never report correlations on tiny samples
- The backend will wrap these in a circuit-breaker check before returning to the frontend
- **Every function must validate input before processing:**
  ```python
  def compute_trigger_correlation(entries):
      if not entries or len(entries) < 5:
          return {}  # Circuit breaker
      # ... rest of logic
  ```

**Function 1 — Trigger Correlation**
- [ ] For each symptom in a user's history, find what triggers appeared in entries within the preceding 24 hours
- [ ] Calculate how often each trigger preceded each symptom vs. how often the symptom occurred without that trigger
- [ ] Conditional probability is fine — you don't need Pearson correlation
- [ ] Only report correlations with at least 5 data points — don't surface noise
- [ ] Output: list of `{symptom, trigger, score (0–1), sample_size}`

**Function 2 — Temporal Patterns**
- [ ] Group entries by day-of-week and time of day (`time_context` field)
- [ ] Find if certain symptoms cluster on specific days or times
- [ ] Example output: fatigue peaks on Monday mornings, headaches cluster on weekend evenings
- [ ] Output: list of `{symptom, peak_day, peak_time, frequency}`

**Function 3 — Severity Trend**
- [ ] For each major symptom, pull the last 14 days of severity scores
- [ ] Fit a simple linear regression — the slope tells you if it's getting better or worse
- [ ] Output: `{symptom, trend ("improving"/"worsening"/"stable"), slope, data_points}`

**Function 4 — `compute_all_stats(user_id)`**
- [ ] Calls the three functions above and combines their output into one JSON blob
- [ ] This is the exact object Noah's insight prompt receives — agree on its shape at the 7pm checkpoint
- [ ] Include `total_entries` and `date_range_days` so the LLM knows how much data it's working with

---

## Phase 5 — API Routes (Fri 10:00pm–Sat 1:00am)
- [ ] Build `GET /api/stats/{user_id}` — calls `compute_all_stats()` and returns the JSON
- [ ] Build `GET /api/entries/{user_id}` — paginated list of entries for the history page, most recent first

---

## Phase 6 — Seed Script (Fri 10:00pm–Sat 1:00am) ⚠️ Critical for demo

**This might be the most important thing you build for the demo.**

Real pattern detection needs weeks of data. You need to fake it. Write `backend/seed.py`.

- [ ] Generate 30 days of fake entries for the demo user
- [ ] **Bake in obvious patterns with real statistical weight:**
  - Caffeine logged → headache appears within 24 hours ~75% of the time
  - Poor sleep logged → fatigue appears the next morning ~80% of the time
  - Stress logged → stomach ache appears same day ~65% of the time
  - Alcohol logged → headache next morning ~85% of the time
- [ ] Vary severity (don't use the same number every time), vary timestamps, vary phrasing in the raw transcript field
- [ ] The patterns need to be strong enough that `compute_all_stats()` actually finds them
- [ ] Running `python seed.py` should fully populate the DB in under 10 seconds
- [ ] **Test: run seed → run `compute_all_stats()` → verify the correlations make sense intuitively**
- [ ] **Note on timeline:** You won't see insights cached until Noah's async code runs (connects to endpoints). This is normal.
  - Seed just populates entries
  - When Noah's `/api/log` endpoints are called, they trigger async insight computation
  - Dashboard will show empty insights until Noah's code runs

---

## Phase 7 — Polish (Sat 8:00–11:00am)
- [ ] Run the seed script fresh on the VM, confirm everything looks right in the DB viewer
- [ ] Verify `compute_all_stats()` output on seeded data makes intuitive sense before handing it to Noah
- [ ] Help Max understand the stats endpoint output if he needs it for charts

---

## 📋 7pm Checkpoint with Noah and Max

**This is a 3-way sync.** All three must be present:

1. **Noah** finalizes the extraction JSON shape
2. **Clayton** finalizes `compute_all_stats()` output shape:
   ```json
   {
     "trigger_correlations": [{"symptom", "trigger", "score", "sample_size"}],
     "temporal_patterns": [{"symptom", "peak_day", "peak_time", "frequency"}],
     "severity_trends": [{"symptom", "trend", "slope", "data_points"}],
     "total_entries": integer,
     "date_range_days": integer
   }
   ```
3. **Max** dictates field names his Recharts components need
   - Clayton **maps his output to match Max's expectations exactly**
   - Example: Max's severity chart needs `[{date: "2026-02-25", severity: 7}]`
   - Clayton modifies output shape to match

Document this agreed contract in the README before moving on.

---

## 💡 Tips
- DBeaver lets you run raw SQL — use it to sanity check your analysis functions before wrapping them in Python
- Your seed data determines whether the demo is impressive or boring. Strong patterns = impressive charts = judges are wowed.
- If a user has fewer than 5 entries for a symptom, skip the correlation analysis for that symptom — reporting on tiny samples will produce misleading results
- Linear regression for the trend function: you just need the slope. Positive = worsening, negative = improving, near zero = stable. stdlib's `statistics` module or a simple manual calculation is fine — no need for numpy unless you want it.
