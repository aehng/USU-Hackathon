# 🤖 Noah — LLM Integration + API Routes

You own the entire backend and everything LLM-related. This is the critical path — Eli and Max's UI can't display real data until your extraction endpoint works, and Clayton's stats can't become insights without your insight route.

**Branch:** `noah/llm-backend`

---

## What You're Building
Two things: the FastAPI server that handles all HTTP routes, and the LLM service layer that powers extraction and insights. The LLM is used in two distinct modes — extraction (every log entry) and insight generation (every dashboard load).

---

## Phase 1 — Setup (~4:00pm Start)
- [ ] Clone the repo and create your branch
- [ ] Set up your FastAPI project structure and install dependencies
- [ ] **Configure Local LLM & Cloudflare Tunnels:** Set up Cloudflare tunnels to expose the LLM running locally on your laptop so the application can route data to and from it.
- [ ] **Environment configuration:**
  - Create `backend/.env` (add to .gitignore immediately):
    ```
    LLM_TUNNEL_URL=[https://your-cloudflare-tunnel-url.trycloudflare.com](https://your-cloudflare-tunnel-url.trycloudflare.com)
    DATABASE_URL=postgresql://postgres:5432/healthtracker
    FRONTEND_URL=[http://192.168.](http://192.168.)x.x:3000
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
