# 🤖 Noah — LLM Integration + API Routes

You own the entire backend and everything LLM-related. This is the critical path — Eli and Max's UI can't display real data until your extraction endpoint works, and Clayton's stats can't become insights without your insight route.

**Branch:** `noah/llm-backend`

---

## What You're Building
Two things: the FastAPI server that handles all HTTP routes, and the LLM service layer that powers extraction and insights. The LLM is used in two distinct modes — extraction (every log entry) and insight generation (every dashboard load).

---

## Phase 1 — Setup (Fri 5:00–6:00pm)
- [ ] Clone the repo and create your branch
- [ ] Set up your FastAPI project structure and install dependencies
- [ ] **Environment configuration:**
  - Create `backend/.env` (add to .gitignore immediately):
    ```
    OPENAI_API_KEY=sk-your-key-here
    DATABASE_URL=postgresql://postgres:5432/healthtracker
    FRONTEND_URL=http://192.168.x.x:3000
    ```
  - Load from .env in your main FastAPI app using `python-dotenv`
  - **Never commit .env to GitHub**
- [ ] **Add CORS middleware to FastAPI:**
  ```python
  from fastapi.middleware.cors import CORSMiddleware
  import os
  
  app.add_middleware(
      CORSMiddleware,
      allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
  This allows frontend at 192.168.x.x:3000 to call backend at 192.168.x.x:8000
- [ ] Run the backend locally and confirm a basic health check route responds
- [ ] Open the auto-generated API docs (FastAPI provides these at `/docs`) — use this to test your routes without needing a frontend

---

## Phase 2 — Extraction Prompt (Fri 6:00–7:00pm) ⚡ Do this first
Everything downstream breaks if extraction is flaky. Get this rock-solid before touching routes.

- [ ] Create a standalone LLM service module (not a route — just a function you call)
- [ ] Write the extraction prompt — takes raw transcript text, returns structured JSON
- [ ] The output must include: `symptoms` (array), `severity` (1–10), `potential_triggers` (array), `mood`, `body_location` (array), `time_context`, `notes`
- [ ] Use OpenAI's JSON mode (`response_format: json_object`) — forces valid JSON every time, no parsing errors
- [ ] Test with at least 10 different voice inputs before moving on:
  - Vague input ("I feel kinda off")
  - No severity mentioned
  - Multiple symptoms at once
  - Mentions of food, sleep, stress as context
  - Non-health rambling
- [ ] If a field can't be determined, it should return null — don't guess
- [ ] Default severity to 5 in your route handler if null comes back — never let null propagate to the DB

---

## Phase 3 — Log Routes (Fri 7:00–9:00pm)
- [ ] Build `POST /api/log/quick`
  - Accepts: `user_id`, `transcript`
  - Calls your extraction function
  - Writes result to DB using Clayton's models
  - Returns the extracted entry so the frontend can display confirmation tags
- [ ] Build `POST /api/log/guided/start`
  - Accepts: `user_id`, `transcript`
  - Runs extraction once on the initial transcript
  - Then generates 2-3 follow-up questions based on what was extracted (another LLM call)
  - Questions should be specific to the symptoms, not generic
  - Returns: `{ extracted: {full extracted JSON}, questions: [array of Q/A objects] }`
  - **Frontend holds the extracted JSON state — this avoids re-running extraction later**
- [ ] Build `POST /api/log/guided/finalize`
  - Accepts: `user_id`, previous `extracted` JSON state, array of new Q&A pairs
  - **Does NOT re-run extraction from scratch.** Instead:
    1. Augment the existing extracted JSON with the new answers
    2. Pass the augmented state to an "extraction update" LLM prompt
    3. The update prompt should only fill in blanks / resolve ambiguities from the new answers
  - **Note on state validation:** Frontend sends extracted JSON back to server.
    - For hackathon: Accept as-is (trust the frontend)
    - For production: Would need HMAC signature or re-extraction to prevent tampering
  - Writes the final entry to DB
  - Immediately triggers background async insight computation (same as quick log)

> **Coordinate with Clayton:** You need his DB models before you can write to the database. Aim to have the extraction function working by 7pm so he can see the data shape.

---

## Phase 4 — Insight Route + Caching (Fri 9:00–11:00pm)
⚠️ **CRITICAL: Insights must be pre-computed and cached, not generated on-demand.**

- [ ] Build `GET /api/insights/{user_id}` — fetch pre-computed insights from DB
  - This endpoint should be instant (just a DB lookup), never call the LLM
  - If `total_entries < 5`, return: `{ insights: [], prediction: null, message: "Not enough data yet. Keep logging to unlock insights!" }`
  - Otherwise, return the cached insights JSON
- [ ] **Insights are generated asynchronously** at the end of `POST /api/log/quick` and `POST /api/log/guided/finalize`
  - **Use FastAPI BackgroundTasks** (simplest for hackathon):
    ```python
    from fastapi import BackgroundTasks
    
    @app.post("/api/log/quick")
    async def log_quick(transcript: str, user_id: str, background_tasks: BackgroundTasks):
        entry = extract_and_write(transcript, user_id)
        background_tasks.add_task(compute_and_cache_insights, user_id)
        return entry  # Return immediately
    
    def compute_and_cache_insights(user_id: str):
        stats = clayton.compute_all_stats(user_id)
        if stats.get("total_entries", 0) < 5:
            insights = {"message": "Not enough data yet"}
        else:
            insights = generate_insights_from_stats(stats)
        db.cache_insights(user_id, insights)
    ```
  - **Note:** BackgroundTasks loses jobs if server crashes. For production use Celery+Redis. For this demo, acceptable.
  - Do not block the log response — return immediately
  - The next dashboard load will show newly computed insights
  - **Cache versioning:** Include entry count in cached insights. Only overwrite if new_count >= old_count.
- [ ] Write the insight prompt — it should produce specific, friendly language, not generic advice
  - Good: "Your migraines appear 68% more often after logging less than 6 hours of sleep."
  - Bad: "Sleep may affect your symptoms."
- [ ] Output shape: `{ insights: [{title, body, icon}], prediction: {title, body, risk_level} }`
- [ ] Coordinate with Clayton on the exact shape of his stats output — agree on this at the 7pm checkpoint (with Max present)

---

## 📋 7pm Checkpoint with Noah, Clayton, and Max

**This is a 3-way sync.** All three must be present:

1. **Noah** finalizes the extraction JSON shape (`symptoms`, `severity`, `triggers`, `mood`, `body_location`, `time_context`, `notes`)
   - This drives Clayton's schema
   - This drives the insights LLM prompt input

2. **Clayton** finalizes the `compute_all_stats()` output shape:
   ```json
   {
     "trigger_correlations": [{"symptom", "trigger", "score", "sample_size"}],
     "temporal_patterns": [{"symptom", "peak_day", "peak_time", "frequency"}],
     "severity_trends": [{"symptom", "trend", "slope", "data_points"}],
     "total_entries": integer,
     "date_range_days": integer
   }
   ```

3. **Max** dictates the exact field names that his Recharts components expect:
   - Severity trend chart: `[{date, severity}, ...]` or `[{name, uv}, ...]`?
   - Triggers bar chart: `[{trigger, count}, ...]` or `[{name, value}, ...]`?
   - Symptom breakdown: `[{symptom, percentage}, ...]` or custom?
   - **Clayton maps his output to match Max's expectations exactly**

Document all three agreed shapes in the README before moving on.

---

## Phase 5 — Edge Cases + Polish (Sat 8:00–11:00am)
- [ ] **Add minimum data check to all analytics endpoints:**
  - If a user has fewer than 5 entries:
    - `GET /api/insights/{user_id}` returns: `{ insights: [], prediction: null, message: "Not enough data yet. Keep logging to unlock insights!" }`
    - `GET /api/stats/{user_id}` returns: `{ total_entries: N, message: "Minimum 5 entries needed for analysis" }`
  - Prevents crashes and hallucination when testing with brand new user IDs
- [ ] **Add error handling to extraction routes:**
  - If LLM call fails: Log the error + raw transcript, return default response:
    ```python
    {
      "symptoms": null,
      "severity": 5,
      "potential_triggers": [],
      "mood": null,
      "body_location": [],
      "time_context": null,
      "notes": "Extraction failed; please edit manually",
      "error": "LLM extraction unavailable"
    }
    ```
  - Frontend shows: "Couldn't extract automatically. Please fill in the details below."
  - Never let LLM errors crash the API (always return 200 with graceful fallback)
- [ ] Add basic request logging so you can see what's coming in during the demo
- [ ] **Monitor OpenAI API costs:**
  - Check usage at https://platform.openai.com/account/usage/overview
  - Seed script: ~$0.05
  - Demo runs (10-20 live entries): ~$0.10-$0.20
  - Budget $5 total; if approaching limit, disable LLM and use mock responses
- [ ] Test every route using the `/docs` UI with Clayton's seeded demo data
- [ ] Stretch goal: `POST /api/chat` — a freeform "ask about your health history" endpoint. Good demo wow factor if you have time.

---

## Tips
- Test your extraction as a plain Python script first — no web server, just call the function directly and print the result
- The `/docs` endpoint FastAPI generates lets you test every route with a form UI — use it constantly, you don't need Postman
- Guided mode's follow-up questions should be generated from the extracted data, not the raw transcript — so you're asking about gaps, not repeating what was already said
- If the LLM returns something unexpected, log it and return a graceful error — don't let it crash

---

## Key Integration Points
| You need from... | What |
|---|---|
| Clayton | DB session / models to write entries (coordinate by 7pm) |
| Clayton | `compute_all_stats(user_id)` function signature and output shape |
| Eli | Nothing — your routes just need to match the API contract in README |
| Max | Nothing — he'll call your insight route once it's up |
