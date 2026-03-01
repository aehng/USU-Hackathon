# 📈 Max — Dashboard + Charts + JSON Validator

Max owned everything the user sees after they log an entry, plus the JSON validation layer that protects the database from malformed LLM output.

**Branch:** `max/dashboard`

---

## What Was Built

### Dashboard (`frontend/src/Dashboard.jsx`)
The main app page. Pulls data from the backend and renders it with Recharts. Key features:
- **Tab navigation** — Main / Guided log / Quick log / History
- **Demo/API toggle** — switch between mock data and live backend data for demos
- **Prediction card** — AI-generated flare-up prediction with risk level
- **LLM guidance card** — AI advice card with disclaimer
- **Insight cards** — 3 discovered pattern cards (tracking consistency, severity average, top symptoms)
- **Severity trend line chart** — last 7 days of daily average severity, formatted `[{date, severity}]`
- **Top triggers bar chart** — horizontal bar chart of the top 3 most frequent triggers, formatted `[{name, value}]`
- **Symptom temporal heatmap** — `TriggerSymptomHeatmap` component showing when symptoms cluster
- **Activity ↔ symptom correlation table** — `ActivitySymptomTable` component
- **"Not enough data" state** — friendly message shown instead of empty/broken charts
- **Loading spinner** while data fetches

### Components Built
- `InsightCard.jsx` — icon, title, body card
- `PredictionCard.jsx` — visually distinct prediction with 🟢/🟡/🔴 risk indicator
- `AdviceCard.jsx` — AI advice with disclaimer text
- `LogHistory.jsx` — scrollable history of past entries with inline editing (edit symptoms, triggers, notes, severity)
- `TriggerSymptomHeatmap.jsx` — heatmap of symptom timing patterns
- `ActivitySymptomTable.jsx` — activity/trigger correlation table

### Mock Data Layer (`frontend/src/mock/dashboardData.js`)
Realistic demo data (mock insights, stats, and "not enough data" fallbacks) so the dashboard looks complete in Demo mode.

### JSON Validator

#### C Validator (`json_filter/`)
A C program using the `cJSON` library that validates LLM JSON output:
- Required fields: `symptoms` (array), `severity` (number 0–10), `potential_triggers` (array)
- Returns `1` if valid, `0` if invalid with a specific error message
- Compiles to `validate_cli` binary (reads from stdin) and `validate_test` test binary
- Full `Makefile` and usage documented in `json_filter/README.md`

#### Python Validator (`backend/validate_voicehealth_json_py.py`) ← **actually used in production**
A Python translation of the C validator that:
- Validates the same required fields with matching error messages
- Also **sanitizes** the data (converts severity=0 → 1, wraps lone strings in arrays, truncates oversized fields)
- Used directly by the FastAPI backend via `from validate_voicehealth_json_py import validate_voicehealth_json_py`
- Has a CLI mode compatible with the C `validate_cli` interface

---

## Key Files
- `frontend/src/Dashboard.jsx` — main dashboard page with all charts and tabs
- `frontend/src/components/` — all UI components (InsightCard, PredictionCard, AdviceCard, LogHistory, TriggerSymptomHeatmap, ActivitySymptomTable)
- `frontend/src/mock/dashboardData.js` — mock data for demo mode
- `json_filter/validate_voicehealth_json.c` — C JSON validator
- `json_filter/validate_voicehealth_json.h` — C header
- `json_filter/validate_cli.c` — C CLI wrapper
- `json_filter/Makefile` — build instructions
- `backend/validate_voicehealth_json_py.py` — Python validator (used by backend)
