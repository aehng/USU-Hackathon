from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
import uvicorn
import os
import requests
import logging
import traceback
from uuid import UUID
import json
import uuid
from typing import Dict, List
import sys
import os

# Adds the parent directory to the search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now you can import as if it were in the same folder
from validate_voicehealth_json import sanitize_voicehealth_data
import json
from models.models import Entry, User

# database imports
from database import SessionLocal
from models.models import Entry, User

# Configure logging to show errors
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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

# In-memory conversation storage for guided log sessions
guided_sessions: Dict[str, List[Dict]] = {}

# --- HELPER FUNCTIONS ---

def call_llm(payload: dict):
    """Handles communicating with the LLM via the Cloudflare tunnel."""
    # ⚠️ DO NOT CHANGE THIS URL UNDER ANY CIRCUMSTANCE - Production LLM endpoint
    llm_base = os.getenv("LLM_SERVER_URL", "https://llm.flairup.dpdns.org").rstrip('/')
    llm_endpoint = f"{llm_base}/generate"
    logger.info("Calling LLM endpoint: %s", llm_endpoint)
    try:
        # Timeout for smaller models (1.7B-4B are ~10-30s, 8B+ can take 30-90s)
        resp = requests.post(llm_endpoint, json={"input": payload}, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        logger.error("LLM request failed: %s", exc)
        if 'resp' in locals():
            logger.error("LLM response: %s - %s", resp.status_code, resp.text)
        raise HTTPException(status_code=502, detail="LLM service unavailable or failed.")
    except ValueError:
        logger.error("LLM returned non-JSON")
        raise HTTPException(status_code=502, detail="LLM returned invalid format.")


def normalize_user_id(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")
    try:
        UUID(str(user_id))
        return user_id
    except ValueError:
        logger.warning("Invalid user_id received (%s); falling back to demo UUID", user_id)
        return "00000000-0000-0000-0000-000000000001"


def call_llm_chat(messages: List[Dict], temperature: float = 0.7):
    """Call LLM with chat messages for conversational guided log."""
    from openai import OpenAI
    
    # ⚠️ DO NOT CHANGE THIS URL UNDER ANY CIRCUMSTANCE - Lemonade LLM endpoint
    lemonade_base = os.getenv("LEMONADE_BASE_URL", "http://localhost:8080/v1")
    model = os.getenv("LLM_MODEL", "Qwen3-1.7B-Hybrid")
    
    client = OpenAI(
        api_key="not-needed",
        base_url=lemonade_base.rstrip("/")
    )
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"LLM chat error: {e}")
        raise HTTPException(status_code=502, detail=f"LLM chat failed: {str(e)}")


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
        logger.error("Database error: %s\n%s", db_exc, traceback.format_exc())
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


@app.post("/api/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Forward audio file to LLM adapter for transcription using Faster-Whisper.
    
    Accepts: audio file (webm, ogg, mp3, wav, etc.)
    Returns: { "text": "transcribed text here" }
    """
    llm_base = os.getenv("LLM_SERVER_URL", "https://llm.flairup.dpdns.org")
    llm_endpoint = f"{llm_base.rstrip('/')}/transcribe"
    
    try:
        # Read the audio file content
        audio_content = await audio.read()
        logger.info(f"Received audio file: {audio.filename}, size: {len(audio_content)} bytes")
        
        # Forward the audio file to the LLM adapter
        files = {"audio": (audio.filename or "recording.webm", audio_content, audio.content_type or "audio/webm")}
        logger.info(f"Forwarding to LLM endpoint: {llm_endpoint}")
        resp = requests.post(llm_endpoint, files=files, timeout=60)
        resp.raise_for_status()
        
        result = resp.json()
        logger.info(f"Transcription successful, text length: {len(result.get('text', ''))}")
        return result
    except requests.RequestException as exc:
        logger.error(f"Transcription request failed: {exc}")
        raise HTTPException(status_code=502, detail=f"Transcription request failed: {str(exc)}")
    except ValueError as exc:
        logger.error(f"Invalid JSON response from transcription service: {exc}")
        raise HTTPException(status_code=502, detail="Transcription service returned non-JSON response")
    except Exception as exc:
        logger.error(f"Unexpected transcription error: {exc}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(exc)}")



@app.post("/api/log/quick")
async def quick_log(request: Request):
    """
    Forward incoming quick-log request to the LLM server, validate via Max's filter, 
    and save result to DB.

    The request JSON should include at least `user_id` and `transcript`.
    After forwarding to the LLM adapter, the returned JSON is expected to
    contain the extracted fields (symptoms, severity, etc.).
    """
    try:
        body = await request.json()
        user_id = normalize_user_id(body.get("user_id"))
        transcript = body.get("transcript")

        if not transcript:
            raise HTTPException(status_code=400, detail="Missing transcript")

        llm_json = call_llm(body)

        llm_json_str = json.dumps(llm_json)
        is_valid, error_msg = validate_voicehealth_json_py(llm_json_str)

        if not is_valid:
            logger.error("LLM output failed validation: %s", error_msg)
            raise HTTPException(status_code=422, detail=f"LLM returned invalid data schema: {error_msg}")

        entry_id = save_entry_to_db(user_id, transcript, llm_json)
        return {"status": "success", "entry_id": str(entry_id), "llm_response": llm_json}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Unhandled exception in quick_log: %s\n%s", exc, traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/guided-log/start")
async def guided_log_start(request: Request):
    """Start a conversational guided log session with LLM asking follow-up questions.
    
    Returns the first follow-up question to gather more complete symptom information.
    """
    try:
        body = await request.json()
        user_id = normalize_user_id(body.get("user_id"))
        transcript = body.get("transcript")

        if not transcript:
            raise HTTPException(status_code=400, detail="Missing transcript")

        # Create new session
        session_id = str(uuid.uuid4())
        
        # System prompt for guided conversation
        system_prompt = (
            "You are a compassionate health assistant helping someone log their symptoms. "
            "Your goal is to gather complete information through natural conversation. "
            "Based on what the user tells you, ask ONE specific follow-up question to:\n"
            "1. Clarify symptom severity (1-10 scale if not mentioned)\n"
            "2. Identify potential triggers (food, stress, activities, environment) - THIS IS MOST IMPORTANT\n"
            "3. Understand timing and duration\n"
            "4. Learn about body location and type of discomfort\n"
            "5. Understand mood and emotional state\n\n"
            "Keep questions short, empathetic, and conversational. "
            "Ask about the MOST important missing information first. "
            "After 2-4 questions, when you have enough information, respond with "
            "EXACTLY this format (including the word COMPLETE): 'COMPLETE:{json_object}' where json_object contains:\n"
            '{"symptoms": ["list"], "severity": 5, "potential_triggers": ["list"], '
            '"mood": "string", "body_location": "string", "time_context": "string", "notes": "string"}'
        )
        
        # Initialize conversation
        guided_sessions[session_id] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Initial log: {transcript}"}
        ]
        
        # Get first question from LLM
        assistant_message = call_llm_chat(guided_sessions[session_id])
        guided_sessions[session_id].append({"role": "assistant", "content": assistant_message})
        
        # Check if already complete (enough info in initial transcript)
        if assistant_message.startswith("COMPLETE:"):
            extracted_data = _extract_completion_data(assistant_message)
            del guided_sessions[session_id]  # Clean up
            return {
                "session_id": session_id,
                "question": None,
                "is_complete": True,
                "extracted_data": extracted_data
            }
        
        return {
            "session_id": session_id,
            "question": assistant_message,
            "is_complete": False,
            "extracted_data": None
        }
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Guided log start failed: %s\n%s", exc, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to start guided log: {str(exc)}")


@app.post("/guided-log/respond")
async def guided_log_respond(request: Request):
    """Submit answer to a follow-up question in the guided log conversation.
    
    Returns the next question or completion with extracted data.
    """
    try:
        body = await request.json()
        session_id = body.get("session_id")
        answer = body.get("answer")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="Missing session_id")
        if not answer:
            raise HTTPException(status_code=400, detail="Missing answer")
            
        if session_id not in guided_sessions:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        # Add user's answer to conversation
        guided_sessions[session_id].append({"role": "user", "content": answer})
        
        # Get next question or completion from LLM
        assistant_message = call_llm_chat(guided_sessions[session_id])
        guided_sessions[session_id].append({"role": "assistant", "content": assistant_message})
        
        # Check if complete
        if assistant_message.startswith("COMPLETE:"):
            extracted_data = _extract_completion_data(assistant_message)
            del guided_sessions[session_id]  # Clean up session
            return {
                "session_id": session_id,
                "question": None,
                "is_complete": True,
                "extracted_data": extracted_data
            }
        
        return {
            "session_id": session_id,
            "question": assistant_message,
            "is_complete": False,
            "extracted_data": None
        }
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Guided log respond failed: %s\n%s", exc, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to process response: {str(exc)}")


def _extract_completion_data(completion_message: str) -> dict:
    """Extract JSON data from COMPLETE:{ } message."""
    try:
        json_str = completion_message.replace("COMPLETE:", "").strip()
        
        # Remove markdown code blocks if present
        if json_str.startswith("```"):
            lines = json_str.split("\n")
            json_lines = []
            in_code_block = False
            for line in lines:
                if line.startswith("```"):
                    in_code_block = not in_code_block
                elif in_code_block:
                    json_lines.append(line)
            json_str = "\n".join(json_lines).strip()
        
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse completion JSON: {completion_message}")
        raise HTTPException(status_code=500, detail="Failed to parse completion data")


# Legacy guided log endpoints (deprecated - use /guided-log/* instead)
@app.post("/api/log/guided/start")
async def guided_log_start_legacy(request: Request):
    """DEPRECATED: Use /guided-log/start instead. Basic stub for compatibility."""
    body = await request.json()
    user_id = normalize_user_id(body.get("user_id"))
    transcript = body.get("transcript")

    if not transcript:
        raise HTTPException(status_code=400, detail="Missing transcript")

    llm_payload = {
        "user_id": user_id,
        "transcript": transcript,
        "mode": "guided_start"
    }

    llm_json = call_llm(llm_payload)

    return {
        "status": "success",
        "message": "Guided log started (legacy endpoint - use /guided-log/start)",
        "extracted_state": llm_json.get("extracted_state", {}),
        "questions": llm_json.get("questions", ["Can you elaborate on your symptoms?"]),
        "data_received": body
    }

@app.post("/api/log/guided/finalize")
async def guided_log_finalize_legacy(request: Request):
    """DEPRECATED: Use conversational /guided-log/* endpoints instead. Finalizes a guided session."""
    body = await request.json()
    user_id = normalize_user_id(body.get("user_id"))
    full_conversation = body.get("full_conversation") # e.g., "User: I hurt. Bot: Where? User: My head."

    if not full_conversation:
        raise HTTPException(status_code=400, detail="Missing full_conversation")

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
        logger.error("Finalize validation failed: %s", error_msg)
        raise HTTPException(status_code=422, detail=f"Final data invalid: {error_msg}")

    # 3. Save to DB
    entry_id = save_entry_to_db(user_id, full_conversation, llm_json)

    return {
        "status": "success",
        "message": "Guided log finalized (legacy endpoint)",
        "entry_id": str(entry_id),
        "symptoms": llm_json.get("symptoms", []),
        "severity": llm_json.get("severity", 0),
        "potential_triggers": llm_json.get("potential_triggers", []),
        "data_received": body
    }

@app.get("/api/insights/{user_id}")
def get_insights(user_id: str):
    """Get dynamic AI insights and analysis for a user"""
    db = SessionLocal()
    try:
        # 1. Get all entries to calculate stats
        entries = db.query(Entry).filter(Entry.user_id == user_id).order_by(Entry.logged_at.desc()).all()
        if not entries:
            return {
                "status": "success",
                "message": "Not enough data yet. Log more entries to see AI patterns.",
                "user_id": user_id,
                "insights": []
            }
        
        current_entry_count = len(entries)
        
        # Calculate basic formatting for the InsightCards
        symptom_counts = {}
        for entry in entries:
            if entry.symptoms:
                for sym in (entry.symptoms if isinstance(entry.symptoms, list) else [entry.symptoms]):
                    symptom_counts[sym] = symptom_counts.get(sym, 0) + 1
                    
        top_symptoms = sorted(symptom_counts.items(), key=lambda x: x[1], reverse=True)
        symptom_body = f"Your most frequent symptom is '{top_symptoms[0][0]}'." if top_symptoms else "No specific symptoms detected yet."
        avg_severity = sum(e.severity for e in entries if e.severity) / len([e for e in entries if e.severity]) if any(e.severity for e in entries) else 0

        formatted_insights = [
            {"id": "1", "title": "Tracking Consistency", "body": f"You have logged {current_entry_count} entries so far.", "icon": "activity"},
            {"id": "2", "title": "Severity Average", "body": f"Your average symptom severity is {avg_severity:.1f}/10.", "icon": "trend"},
            {"id": "3", "title": "Top Symptoms", "body": symptom_body, "icon": "alert"}
        ]

        # 2. Build the payload for the Lemonade LLM Server
        # We pass the recent stats so the LLM has context to generate personalized advice
        recent_entries = entries[:5]
        llm_payload = {
            "mode": "generate_insights",
            "user_id": user_id,
            "context": {
                "total_entries": current_entry_count,
                "average_severity": round(avg_severity, 1),
                "recent_symptoms": [s[0] for s in top_symptoms[:3]],
                "latest_notes": recent_entries[0].raw_transcript if recent_entries else ""
            },
            "prompt": "Based on the user's recent health data, provide a short prediction and medical advice. Return ONLY valid JSON with two objects: 'prediction' (keys: title, body, riskLevel) and 'advice' (keys: title, body, disclaimer)."
        }

        # 3. Call the LLM
        # (If you want to use the cache table later, wrap this call in an if-statement!)
        try:
            llm_response = call_llm(llm_payload)
        except Exception as llm_error:
            logger.error(f"LLM Insight Generation Failed: {llm_error}")
            # Safe fallback so the dashboard doesn't crash if the LLM times out
            llm_response = {
                "prediction": {"title": "AI Offline", "body": "Unable to reach the AI server for predictions.", "riskLevel": "unknown"},
                "advice": {"title": "AI Offline", "body": "Please try again in a few moments.", "disclaimer": "Connection error."}
            }

        # 4. Return the combined data to React
        return {
            "status": "success",
            "user_id": user_id,
            "insights": formatted_insights,
            "prediction": llm_response.get("prediction", {}),
            "advice": llm_response.get("advice", {})
        }
        
    except Exception as e:
        logger.error(f"Error getting insights: {e}\n{traceback.format_exc()}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@app.get("/api/stats/{user_id}")
def get_stats(user_id: str):
    """Get statistics for a user formatted for Recharts"""
    db = SessionLocal()
    try:
        entries = db.query(Entry).filter(Entry.user_id == user_id).all()
        
        if not entries:
            return {
                "status": "success",
                "user_id": user_id,
                "total_entries": 0,
                "message": "No entries yet"
            }
        
        # 1. Format Severity Trends for Recharts [{date: "...", severity: X}]
        severity_trends = []
        for e in entries:
            if e.severity and e.logged_at:
                severity_trends.append({
                    "date": e.logged_at.strftime("%Y-%m-%d"),
                    "severity": e.severity
                })
        # Sort by date and grab the last 7
        severity_trends = sorted(severity_trends, key=lambda x: x["date"])[-7:]

        # 2. Format Trigger Correlations for Recharts [{name: "...", value: X}]
        all_triggers = []
        for entry in entries:
            if entry.potential_triggers:
                triggers = entry.potential_triggers if isinstance(entry.potential_triggers, list) else [entry.potential_triggers]
                all_triggers.extend(triggers)
                
        trigger_counts = {}
        for t in all_triggers:
            trigger_counts[t] = trigger_counts.get(t, 0) + 1
            
        trigger_correlations = [{"name": k, "value": v} for k, v in trigger_counts.items()]
        # Sort by highest count and grab the top 5
        trigger_correlations = sorted(trigger_correlations, key=lambda x: x["value"], reverse=True)[:5]

        return {
            "status": "success",
            "user_id": user_id,
            "total_entries": len(entries),
            "severity_trends": severity_trends,
            "trigger_correlations": trigger_correlations
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
    # ⚠️ DO NOT CHANGE PORT 8000 UNDER ANY CIRCUMSTANCE - Container internal port
    uvicorn.run(app, host="0.0.0.0", port=8000)