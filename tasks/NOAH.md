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
- [ ] Add your OpenAI API key to your local environment file
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
  - Runs extraction first
  - Then generates 2-3 follow-up questions based on what was extracted (another LLM call)
  - Questions should be specific to the symptoms, not generic
  - Returns: `{ extracted, questions }`
- [ ] Build `POST /api/log/guided/finalize`
  - Accepts: `user_id`, original `transcript`, array of Q&A pairs
  - Combines everything into one text blob
  - Runs extraction on the combined text
  - Writes final entry to DB

> **Coordinate with Clayton:** You need his DB models before you can write to the database. Aim to have the extraction function working by 7pm so he can see the data shape.

---

## Phase 4 — Insight Route (Fri 9:00–11:00pm)
- [ ] Build `GET /api/insights/{user_id}`
  - Calls Clayton's `compute_all_stats(user_id)` function
  - Passes the stats JSON into an insight generation prompt
  - Returns 3 insight cards + 1 prediction card
- [ ] Write the insight prompt — it should produce specific, friendly language, not generic advice
  - Good: "Your migraines appear 68% more often after logging less than 6 hours of sleep."
  - Bad: "Sleep may affect your symptoms."
- [ ] Output shape: `{ insights: [{title, body, icon}], prediction: {title, body, risk_level} }`
- [ ] Coordinate with Clayton on the exact shape of his stats output — agree on this at the 7pm checkpoint

---

## Phase 5 — Polish (Sat 8:00–11:00am)
- [ ] Add error handling to every route — a bad LLM response should never crash the API
- [ ] Add basic request logging so you can see what's coming in during the demo
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
