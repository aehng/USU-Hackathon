from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import requests
import logging
import json

# database imports
from database import SessionLocal
from models.models import Entry, User

# Import Max's validator
from validate_voicehealth_json_py import validate_voicehealth_json_py

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

# --- HELPER FUNCTIONS ---

def call_llm(payload: dict):
    """Handles communicating with the LLM via the Cloudflare tunnel."""
    llm_base = os.getenv("LLM_SERVER_URL", "https://llm.flairup.dpdns.org").rstrip('/')
    llm_endpoint = f"{llm_base}/generate"
    try:
        # Timeout for smaller models (1.7B-4B are ~10-30s, 8B+ can take 30-90s)
        resp = requests.post(llm_endpoint, json={"input": payload}, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        logging.error(f"LLM request failed: {exc}")
        if 'resp' in locals():
            logging.error(f"Response: {resp.status_code} - {resp.text}")
        raise HTTPException(status_code=502, detail="LLM service unavailable or failed.")
    except ValueError:
        logging.error("LLM returned non-JSON")
        raise HTTPException(status_code=502, detail="LLM returned invalid format.")

def save_entry_to_db(user_id: str, transcript: str, llm_data: dict):
    """Handles creating/finding the user and saving the health entry to the database."""
    db = SessionLocal()
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
            symptoms=llm_data.get("symptoms"),
            severity=llm_data.get("severity"),
            potential_triggers=llm_data.get("potential_triggers"),
            mood=llm_data.get("mood"),
            body_location=llm_data.get("body_location"),
            time_context=llm_data.get("time_context"),
            notes=llm_data.get("notes"),
        )
        db.add(entry)
        db.commit()
        return entry.id
    except Exception as db_exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {db_exc}")
    finally:
        db.close()

# --- API ENDPOINTS ---

@app.get("/")
def read_root():
    return {"status": "ok", "message": "VoiceHealth Tracker API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/log/quick")
async def quick_log(request: Request):
    """
    Forward incoming quick-log request to the LLM server, validate via Max's filter, 
    and save result to DB.

    The request JSON should include at least `user_id` and `transcript`.
    After forwarding to the LLM adapter, the returned JSON is expected to
    contain the extracted fields (symptoms, severity, etc.).
    """
    body = await request.json()
    user_id = body.get("user_id")
    transcript = body.get("transcript")

    if not user_id or not transcript:
        raise HTTPException(status_code=400, detail="Missing user_id or transcript")

    # 1. Ask LLM to extract data
    llm_json = call_llm(body)

    # 2. Validate extracted data
    llm_json_str = json.dumps(llm_json)
    is_valid, error_msg = validate_voicehealth_json_py(llm_json_str)

    if not is_valid:
        logging.error(f"LLM output failed validation: {error_msg}")
        raise HTTPException(status_code=422, detail=f"LLM returned invalid data schema: {error_msg}")

    # 3. Save to DB
    entry_id = save_entry_to_db(user_id, transcript, llm_json)

    return {"status": "success", "entry_id": str(entry_id), "llm_response": llm_json}

@app.post("/api/log/guided/start")
async def guided_log_start(request: Request):
    """Starts a guided logging session by asking the LLM for follow-up questions."""
    body = await request.json()
    user_id = body.get("user_id")
    transcript = body.get("transcript")

    # Pass a "mode" hint so the LLM knows to ask questions instead of just extracting
    llm_payload = {
        "user_id": user_id,
        "transcript": transcript,
        "mode": "guided_start" 
    }
    
    llm_json = call_llm(llm_payload)

    return {
        "status": "success",
        "message": "Guided log started",
        "extracted_state": llm_json.get("extracted_state", {}),
        "questions": llm_json.get("questions", ["Can you elaborate on your symptoms?"]),
        "data_received": body
    }

@app.post("/api/log/guided/finalize")
async def guided_log_finalize(request: Request):
    """Finalizes a guided session, extracts data, validates it, and saves it."""
    body = await request.json()
    user_id = body.get("user_id")
    full_conversation = body.get("full_conversation") # e.g., "User: I hurt. Bot: Where? User: My head."

    if not user_id or not full_conversation:
        raise HTTPException(status_code=400, detail="Missing user_id or full_conversation")

    llm_payload = {
        "user_id": user_id,
        "transcript": full_conversation,
        "mode": "guided_finalize"
    }

    # 1. Ask LLM to extract final data from the full conversation
    llm_json = call_llm(llm_payload)

    # 2. Validate the final extraction
    llm_json_str = json.dumps(llm_json)
    is_valid, error_msg = validate_voicehealth_json_py(llm_json_str)

    if not is_valid:
        logging.error(f"Finalize validation failed: {error_msg}")
        raise HTTPException(status_code=422, detail=f"Final data invalid: {error_msg}")

    # 3. Save to DB
    entry_id = save_entry_to_db(user_id, full_conversation, llm_json)

    return {
        "status": "success",
        "message": "Guided log finalized",
        "entry_id": str(entry_id),
        "symptoms": llm_json.get("symptoms", []),
        "severity": llm_json.get("severity", 0),
        "potential_triggers": llm_json.get("potential_triggers", []),
        "data_received": body
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