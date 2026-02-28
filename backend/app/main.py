from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
import uvicorn
import os
import requests
import logging
import traceback

# database imports
from database import SessionLocal
from models.models import Entry, User

# Configure logging to show errors
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
    return {"status": "ok", "message": "VoiceHealth Tracker API"}

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
    try:
        body = await request.json()
        user_id = body.get("user_id")
        transcript = body.get("transcript")

        # default location for the LLM adapter via Cloudflare tunnel
        # use HTTPS so TLS is terminated by the tunnel
        llm_base = os.getenv("LLM_SERVER_URL", "https://llm.flairup.dpdns.org")
        llm_endpoint = f"{llm_base.rstrip('/')}/generate"
        logger.info(f"Calling LLM endpoint: {llm_endpoint}")
        try:
            # Timeout for smaller models (1.7B-4B are ~10-30s, 8B+ can take 30-90s)
            resp = requests.post(llm_endpoint, json={"input": body}, timeout=60)
            resp.raise_for_status()
            llm_json = resp.json()
        except requests.RequestException as exc:
            logger.error(f"LLM request failed: {exc}")
            raise HTTPException(status_code=502, detail=f"LLM request failed: {exc}")
        except ValueError as exc:
            logger.error(f"LLM returned non-JSON response: {exc}")
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
            logger.info(f"Saved entry {entry_id} for user {user_id}")
        except Exception as db_exc:
            logger.error(f"Database error: {db_exc}\n{traceback.format_exc()}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {db_exc}")
        finally:
            db.close()

        return {"status": "success", "entry_id": str(entry_id), "llm_response": llm_json}
    except Exception as e:
        logger.error(f"Unhandled exception in quick_log: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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

@app.get("/api/insights/{user_id}")
def get_insights(user_id: str):
    """Get insights and analysis for a user"""
    db = SessionLocal()
    try:
        entries = db.query(Entry).filter(Entry.user_id == user_id).all()
        if not entries:
            return {
                "status": "success",
                "message": "No entries yet - log some symptoms to see insights",
                "user_id": user_id,
                "insights": []
            }
        
        # Basic analysis: count symptom frequencies
        symptom_counts = {}
        for entry in entries:
            if entry.symptoms:
                for sym in (entry.symptoms if isinstance(entry.symptoms, list) else [entry.symptoms]):
                    symptom_counts[sym] = symptom_counts.get(sym, 0) + 1
        
        # Average severity
        avg_severity = sum(e.severity for e in entries if e.severity) / len([e for e in entries if e.severity]) if any(e.severity for e in entries) else None
        
        return {
            "status": "success",
            "user_id": user_id,
            "insights": [
                {"type": "symptom_frequency", "data": symptom_counts},
                {"type": "average_severity", "value": avg_severity},
                {"type": "total_entries", "value": len(entries)}
            ]
        }
    except Exception as e:
        logger.error(f"Error getting insights: {e}\n{traceback.format_exc()}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@app.get("/api/stats/{user_id}")
def get_stats(user_id: str):
    """Get statistics for a user"""
    db = SessionLocal()
    try:
        entries = db.query(Entry).filter(Entry.user_id == user_id).all()
        
        if not entries:
            return {
                "status": "success",
                "user_id": user_id,
                "total_entries": 0,
                "avg_severity": None,
                "message": "No entries yet"
            }
        
        # Calculate stats
        total_entries = len(entries)
        avg_severity = sum(e.severity for e in entries if e.severity) / len([e for e in entries if e.severity]) if any(e.severity for e in entries) else None
        
        # Collect all triggers
        all_triggers = []
        for entry in entries:
            if entry.potential_triggers:
                triggers = entry.potential_triggers if isinstance(entry.potential_triggers, list) else [entry.potential_triggers]
                all_triggers.extend(triggers)
        
        return {
            "status": "success",
            "user_id": user_id,
            "total_entries": total_entries,
            "avg_severity": avg_severity,
            "top_triggers": list(set(all_triggers))[:5] if all_triggers else [],
            "date_created": str(entries[0].created_at) if entries else None
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}\n{traceback.format_exc()}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@app.get("/api/history/{user_id}")
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
