# 🤖 Noah — LLM Integration + API Routes + History/Edit Tab + Cloudflare

Noah owned the entire backend, the LLM integration, the History/Edit frontend tab, and the Cloudflare infrastructure that made the app publicly accessible during the hackathon.

**Branch:** `noah/llm-backend`

---

## What Was Built

### Lemonade LLM Adapter (`backend/lemonade_adapter.py`)
A custom FastAPI server running on Noah's laptop that bridges the main backend to the Qwen3-1.7B-Hybrid local LLM via the [Lemonade](https://github.com/lemonade-sdk/lemonade) server. Exposes an OpenAI-compatible API, including:
- `POST /generate` — symptom extraction from transcripts
- `POST /transcribe` — audio-to-text via Faster-Whisper
- `POST /v1/chat/completions` — conversational guided log with multi-turn dialogue
- `POST /chat` — simplified chat endpoint

### FastAPI Backend (`backend/app/main.py`)
All HTTP routes:
- `GET /health` — health check
- `POST /api/transcribe` — proxies audio to Faster-Whisper in the LLM adapter
- `POST /api/log/quick` — transcript → LLM extraction → validation → DB write
- `POST /api/guided-log/start` — starts conversational guided session, returns first follow-up question
- `POST /api/guided-log/respond` — submits answer, returns next question or completion
- `POST /api/guided-log/finalize` — finalizes conversation, extracts data, writes to DB
- `GET /api/insights/{user_id}` — generates AI insight cards + prediction from user history
- `GET /api/stats/{user_id}` — returns chart-ready stats (severity trends, trigger counts)
- `GET /api/history/{user_id}` — returns all log entries for the history page
- `PUT /api/entries/{entry_id}` — edits an existing log entry

### History / Database Display & Edit Tab (`frontend/src/components/LogHistory.jsx`)
Built the **History tab** — the frontend view that lets users browse and edit their past log entries:
- Scrollable list of all past entries, most recent first
- Each row shows date/time, symptom tags (colored by severity), severity badge, triggers, and notes
- Inline editing: users can update symptoms, triggers, notes, and severity directly in the UI
- Calls `GET /api/history/{user_id}` and `PUT /api/entries/{entry_id}` to fetch and persist changes

### Key Backend Features
- **CORS** configured to allow all origins (suitable for hackathon deployment)
- **Canonical trigger list** and alias map for normalizing LLM trigger output
- **Trigger taxonomy pipeline** — secondary LLM call classifies raw trigger strings to canonical root-cause categories; results are cached in the `trigger_taxonomy` DB table
- **`sanitize_llm_data()`** — fixes common LLM output issues (severity=0, wrong types) before validation
- **`normalize_user_id()`** — falls back to the demo UUID for invalid user IDs
- **In-memory guided session storage** (`guided_sessions` dict) holds multi-turn conversations

### Cloudflare Tunnel Management
Set up and managed all **Cloudflare Tunnels** that exposed the hackathon VM to the public internet:
- `https://flairup.dpdns.org` — React frontend
- `https://api.flairup.dpdns.org` — FastAPI backend
- `https://llm.flairup.dpdns.org` — Lemonade LLM adapter (running on Noah's laptop)

> ⚠️ All three domains are now offline — they were served from a hackathon VM and laptop that are no longer running. To run the app locally, use Docker Compose (see README).

---

## Key Files
- `backend/app/main.py` — all FastAPI routes and helper functions
- `backend/lemonade_adapter.py` — LLM adapter (Qwen3 + Faster-Whisper)
- `frontend/src/components/LogHistory.jsx` — History/edit tab component
- `backend/requirements.txt` — Python dependencies
- `backend/Dockerfile` — containerized backend

