# 🤖 Noah — LLM Integration + API Routes + Audio Transcription

Noah owned the entire backend, the LLM integration, and the Cloudflare infrastructure. This was the critical path — every other feature depended on the extraction endpoint working correctly.

**Branch:** `noah/llm-backend`

---

## What Was Built

### Lemonade LLM Adapter (`backend/lemonade_adapter.py`)
A custom FastAPI server running on Noah's laptop that bridges the main backend to the Qwen3-1.7B-Hybrid local LLM via the [Lemonade](https://github.com/lemonade-sdk/lemonade) server. Exposes an OpenAI-compatible API, including:
- `POST /generate` — symptom extraction from transcripts
- `POST /transcribe` — audio-to-text via Faster-Whisper
- `POST /v1/chat/completions` — conversational guided log with multi-turn dialogue
- `POST /chat` — simplified chat endpoint

The adapter is exposed publicly via **Cloudflare Tunnels** at `https://llm.flairup.dpdns.org`.

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

### Key Backend Features
- **CORS** configured to allow all origins (suitable for hackathon deployment)
- **Canonical trigger list** and alias map for normalizing LLM trigger output
- **Trigger taxonomy pipeline** — secondary LLM call classifies raw trigger strings to canonical root-cause categories; results are cached in the `trigger_taxonomy` DB table
- **`sanitize_llm_data()`** — fixes common LLM output issues (severity=0, wrong types) before validation
- **`normalize_user_id()`** — falls back to the demo UUID for invalid user IDs
- **In-memory guided session storage** (`guided_sessions` dict) holds multi-turn conversations

### Deployment
- Backend served at `https://api.flairup.dpdns.org` via Cloudflare Tunnels
- LLM adapter served at `https://llm.flairup.dpdns.org` from Noah's laptop

---

## Key Files
- `backend/app/main.py` — all FastAPI routes and helper functions
- `backend/lemonade_adapter.py` — LLM adapter (Qwen3 + Faster-Whisper)
- `backend/requirements.txt` — Python dependencies
- `backend/Dockerfile` — containerized backend

