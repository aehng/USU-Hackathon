# 🩺 FlairUp — VoiceHealth Tracker
Voice-activated health logging with automatic trigger detection and flare-up prediction. Speak your symptoms, skip the forms. The app finds patterns you'd never notice yourself.

**Live at:** https://flairup.dpdns.org

## 👥 Team
| Person | Role |
|---|---|
| Eli | Frontend — Voice UI (MediaRecorder + Faster-Whisper) + Log Screen + Project Coordination |
| Noah | Backend — Lemonade LLM Adapter + Cloudflare Tunnels + API Routes + Audio Transcription |
| Clayton | Backend — Database Schema + Analysis Engine + Trigger Taxonomy Pipeline |
| Max | Frontend & Validation — Dashboard + Charts + JSON Validator (C + Python) |

## 🏗️ Stack
| Layer | Tech | Why |
|---|---|---|
| Frontend | React + Vite + Tailwind CSS | Fast setup, works on any phone browser |
| Backend | FastAPI (Python) | Same language as LLM work, auto-generates API docs |
| Database | PostgreSQL 15 | Handles array types natively (symptom/trigger lists) |
| Voice | MediaRecorder API + Faster-Whisper | Records audio in-browser, transcribed server-side for reliable cross-browser support |
| LLM | Qwen3-1.7B-Hybrid via Lemonade | Noah runs the model locally via the Lemonade server, tunneled to the app |
| LLM Adapter | `lemonade_adapter.py` (FastAPI) | Custom OpenAI-compatible adapter bridging the FastAPI backend and Lemonade |
| Validation | Python JSON Validator (`validate_voicehealth_json_py.py`) | Validates and sanitizes LLM JSON output before writing to DB |
| Runtime | Docker Compose | Everyone runs the same environment |

⚠️ Web app, not Android. A React app works on every phone browser and deploys in seconds.
⚠️ Voice recording uses the MediaRecorder API (works in Chrome, Edge, and Firefox) with Faster-Whisper for transcription. Web Speech API is no longer used.

## 🔒 Security & Data Note
This app uses a single shared demo user (`00000000-0000-0000-0000-000000000001`) for all entries. Full user authentication is not implemented in this hackathon build.

## 🌐 Production & Local Access

| Service | Address |
|---|---|
| Frontend (prod) | https://flairup.dpdns.org |
| Backend API (prod) | https://api.flairup.dpdns.org |
| LLM Adapter (Noah's laptop) | https://llm.flairup.dpdns.org |
| Frontend (local Docker) | http://localhost:5173 |
| Backend API (local Docker) | http://localhost:8001 |
| API Docs (local) | http://localhost:8001/docs |

### 🔌 Port Allocations
| Port | Service | Owner | Description |
|---|---|---|---|
| `5173` | Frontend | Eli/Max | React Vite Development Server |
| `5432` | Database | Clayton | PostgreSQL Connection |
| `8000` | Lemonade Adapter | Noah | LLM adapter internal port (mapped to 8001 externally) |
| `8001` | Backend API | Noah/Clayton | FastAPI Web Server (external) |

## 🗄️ Database Schema

The PostgreSQL schema is defined in `db/init.sql` and includes the following tables:
| Table | Description |
|---|---|
| `users` | Stores users. A hardcoded demo user (`00000000-0000-0000-0000-000000000001`) is seeded on startup. |
| `entries` | Stores raw logs, extracted arrays (`symptoms`, `potential_triggers`), and severity. Indexed for fast querying. |
| `correlations` | Tracks statistical relationships between symptoms and triggers, including correlation scores and sample sizes. |
| `insights_cache` | Stores pre-computed insights as JSON. Written asynchronously after LLM extraction to avoid blocking the UI. |
| `trigger_taxonomy` | Maps raw LLM trigger strings to canonical root-cause categories per user (e.g., "drank 2 monsters" → "Caffeine"). LLM-assisted mapping is cached here to avoid repeat LLM calls. |

## 🏛️ Architecture

```text
[User's Phone — Any Modern Browser]
        |
   Speaks into mic → MediaRecorder captures audio → sent to backend
        |
[React Frontend — Eli + Max]
        |
        | POST /api/transcribe  (audio blob → Faster-Whisper → transcript)
        | POST /api/log/quick   (transcript → LLM extraction → DB write)
        | POST /api/guided-log/start → respond → finalize  (conversational log)
        ↓
[FastAPI Backend — Noah + Clayton]
        |                    |
        ↓                    ↓
  [PostgreSQL]        [Lemonade Adapter — Noah's Laptop]
    stores                OpenAI-compatible API wrapping
    entries               Qwen3-1.7B-Hybrid local LLM
    trigger               ├─ /generate (symptom extraction)
    taxonomy              ├─ /transcribe (Faster-Whisper)
    insights              └─ /v1/chat/completions (guided log)
    cache
        |                    ↓
        |           [Python JSON Validator]
        |             validates + sanitizes
        |             LLM output before DB write
        ↓
[Analysis Engine — Clayton]
  queries DB, runs correlations, finds patterns
  computes: trigger_correlations, temporal_patterns,
            severity_trends, symptom_frequency
        |
        ↓
[Dashboard — React — Max]
  shows insight cards, charts, trigger bars,
  severity trend, prediction, entry history
```

## 🔀 How Development Works
Everyone codes on their own laptop in their own editor. The VM is the shared server.
Git is your sync mechanism. Docker is the runtime.

```text
Your Laptop (VSCode)
  → write code
  → git push to GitHub
  
VM
  → git pull from GitHub
  → docker compose up --build
  → app live at flairup.dpdns.org
```

* **Frontend devs (Eli + Max):** Run Vite locally on your laptop, pointed at the production or local backend. You'll see changes instantly without touching the VM.
* **Backend devs (Noah + Clayton):** Run FastAPI locally, pointed at the VM's Postgres. Or run everything on the VM via Docker. Ensure Cloudflare tunnels route properly to Noah's local Lemonade LLM adapter.
* **Pulling to the VM:** Manual every 20–30 minutes is fine. No need to over-engineer this.

---

## 🌿 Branch Strategy
| Branch | Owner |
|---|---|
| `main` | Stable — what the VM runs |
| `eli/voice-ui` | Eli |
| `noah/llm-backend` | Noah |
| `clayton/db-analysis` | Clayton |
| `max/dashboard` | Max |

Merge to `main` when something works end-to-end. VM pulls from `main`.

⚠️ Ask Eli before changing `DEMO_USER_ID` or `API_BASE_URL` in the frontend.

---

## 📡 API Endpoints

| Method | Route | Owner | Description |
|---|---|---|---|
| GET | `/health` | Noah | Health check — server is up |
| POST | `/api/transcribe` | Noah | Upload audio blob → Faster-Whisper → returns transcript text |
| POST | `/api/log/quick` | Noah | Log entry from transcript, returns extracted data |
| POST | `/api/guided-log/start` | Noah | Start a conversational guided log, returns first follow-up question |
| POST | `/api/guided-log/respond` | Noah | Submit answer to a follow-up question, returns next question or completion |
| POST | `/api/guided-log/finalize` | Noah | Finalize guided session: extract JSON from conversation, write to DB |
| GET | `/api/insights/{user_id}` | Noah | Return AI-generated insight cards, prediction, and advice |
| GET | `/api/stats/{user_id}` | Clayton | Return stats for charts (severity trends, trigger counts) |
| GET | `/api/history/{user_id}` | Clayton | Return all log entries for the history page |
| PUT | `/api/entries/{entry_id}` | Clayton | Edit an existing log entry (symptoms, triggers, notes, severity) |

> The legacy `/api/log/guided/start` and `/api/log/guided/finalize` endpoints are still present for compatibility but deprecated. Use `/api/guided-log/*` instead.

---

## 📋 JSON Contract

### Log entry (what gets stored):
```json
{
  "user_id": "uuid",
  "raw_transcript": "string",
  "symptoms": ["symptom1", "symptom2"],
  "severity": 5,
  "potential_triggers": ["Caffeine", "Stress"],
  "mood": "string or null",
  "body_location": ["head", "stomach"],
  "time_context": "morning",
  "notes": "string",
  "logged_at": "timestamp"
}
```

> Triggers are normalized through the **trigger taxonomy pipeline**: raw strings from the LLM (e.g. "drank 2 monsters") are mapped to canonical root causes (e.g. "Caffeine") via a secondary LLM call. Mappings are cached in `trigger_taxonomy` per user.

### Stats output (`GET /api/stats/{user_id}`):
```json
{
  "status": "success",
  "user_id": "uuid",
  "total_entries": 42,
  "severity_trends": [
    {"date": "2026-02-25", "severity": 7}
  ],
  "trigger_correlations": [
    {"name": "Caffeine", "value": 14}
  ]
}
```

### Insights output (`GET /api/insights/{user_id}`):
```json
{
  "status": "success",
  "user_id": "uuid",
  "insights": [
    {"id": "1", "title": "Tracking Consistency", "body": "...", "icon": "activity"}
  ],
  "prediction": {"title": "...", "body": "...", "riskLevel": "medium"},
  "advice": {"title": "...", "body": "...", "disclaimer": "..."}
}
```

⚠️ If a user has no entries, both endpoints return a `"message"` field instead of data arrays, and the frontend shows a friendly "not enough data" message.

---

## 📁 Team Summaries
- [Eli — Voice UI + Coordination](./tasks/ELI.md)
- [Noah — LLM + API Routes](./tasks/NOAH.md)
- [Clayton — Database + Analysis](./tasks/CLAYTON.md)
- [Max — Dashboard + Charts](./tasks/MAX.md)
