from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import requests

# database imports
from database import SessionLocal
from models.models import Entry, User

app = FastAPI(title="VoiceHealth Tracker API")

# Enable CORS for frontend
# Note: when running behind Cloudflare tunnels, the frontend will talk to
# `https://flairup.dpdns.org` and the LLM adapter is reachable at
# `https://llm.flairup.dpdns.org`.  These are the defaults for
# LLM_SERVER_URL and normal API traffic.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "VoiceHealth Tracker API - Placeholder"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Placeholder routes - Noah will implement these
@app.post("/api/log/quick")
async def quick_log(request: Request):
    """Forward incoming quick-log request to the LLM server, save result to DB.

    The request JSON should include at least ``user_id`` and ``transcript``.
    After forwarding to the LLM adapter, the returned JSON is expected to
    contain the extracted fields (symptoms, severity, etc.). We persist an
    ``Entry`` record using those values.
    """
    body = await request.json()
    user_id = body.get("user_id")
    transcript = body.get("transcript")

    # default location for the LLM adapter via Cloudflare tunnel
    # use HTTPS so TLS is terminated by the tunnel
    llm_base = os.getenv("LLM_SERVER_URL", "https://llm.flairup.dpdns.org")
    llm_endpoint = f"{llm_base.rstrip('/')}/generate"
    try:
        resp = requests.post(llm_endpoint, json={"input": body}, timeout=15)
        resp.raise_for_status()
        llm_json = resp.json()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {exc}")
    except ValueError:
        raise HTTPException(status_code=502, detail="LLM returned non-JSON response")

    # record entry in database
    db = SessionLocal()
    entry_id = None
    try:
        if user_id:
            # ensure user exists
            existing = db.query(User).get(user_id)
            if not existing:
                new_user = User(id=user_id)
                db.add(new_user)
                db.commit()
        entry = Entry(
            user_id=user_id,
            raw_transcript=transcript,
            symptoms=llm_json.get("symptoms"),
            severity=llm_json.get("severity"),
            potential_triggers=llm_json.get("potential_triggers"),
            mood=llm_json.get("mood"),
            body_location=llm_json.get("body_location"),
            time_context=llm_json.get("time_context"),
            notes=llm_json.get("notes"),
        )
        db.add(entry)
        db.commit()
        entry_id = entry.id
    except Exception as db_exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {db_exc}")
    finally:
        db.close()

    return {"status": "success", "entry_id": str(entry_id), "llm_response": llm_json}

@app.post("/api/log/guided/start")
def guided_log_start(data: dict):
    """Placeholder for guided log start endpoint"""
    return {
        "status": "success",
        "message": "Guided log start placeholder - Noah will implement",
        "extracted_state": {"raw": "placeholder"},
        "questions": [
            "On a scale of 1-10, how severe is your pain?",
            "Have you noticed any triggers or patterns?"
        ],
        "data_received": data
    }

@app.post("/api/log/guided/finalize")
def guided_log_finalize(data: dict):
    """Placeholder for guided log finalize endpoint"""
    return {
        "status": "success",
        "message": "Guided log finalized - Noah will implement",
        "symptoms": ["fatigue"],
        "severity": 5,
        "potential_triggers": ["lack of sleep"],
        "data_received": data
    }

@app.get("/api/insights")
def get_insights(user_id: str):
    """Placeholder for insights endpoint"""
    return {
        "status": "success",
        "message": "Insights placeholder - Clayton & Noah will implement",
        "user_id": user_id,
        "insights": []
    }

@app.get("/api/history")
def get_history(user_id: str):
    """Placeholder for history endpoint"""
    return {
        "status": "success",
        "message": "History placeholder - Clayton & Noah will implement",
        "user_id": user_id,
        "entries": []
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
