import os
import sys
import logging
import traceback
import json
import uuid
from typing import Dict, List
from uuid import UUID

import uvicorn
import requests
from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

# 1. Update path FIRST
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 2. Perform local imports (Check filenames!)
from validate_voicehealth_json_py import validate_voicehealth_json_py
from models.models import Entry, User, TriggerTaxonomy
from database import SessionLocal 

# Configure logging
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

# In-memory conversation storage for guided log sessions
guided_sessions: Dict[str, List[Dict]] = {}

# Canonical trigger vocabulary to reduce inconsistent labels across logs.
CANONICAL_TRIGGER_LIST = [
    "stress",
    "anxiety",
    "lack of sleep",
    "caffeine",
    "alcohol",
    "dehydration",
    "dairy",
    "gluten",
    "sugar",
    "spicy food",
    "processed food",
    "allergens",
    "weather change",
    "air quality",
    "hormonal changes",
    "illness",
    "medication",
    "exercise",
    "overexertion",
    "injury",
    "screen time",
    "bright lights",
    "loud noise",
]

TRIGGER_ALIAS_TO_CANONICAL = {
    "stressful experience": "stress",
    "stressful situation": "stress",
    "work stress": "stress",
    "anxious": "anxiety",
    "worry": "anxiety",
    "poor sleep": "lack of sleep",
    "insomnia": "lack of sleep",
    "coffee": "caffeine",
    "energy drink": "caffeine",
    "tea": "caffeine",
    "milk": "dairy",
    "cheese": "dairy",
    "bread": "gluten",
    "pollen": "allergens",
    "dust": "allergens",
    "pollution": "air quality",
    "humid weather": "weather change",
    "period": "hormonal changes",
    "menstrual cycle": "hormonal changes",
    "workout": "exercise",
    "heavy exercise": "overexertion",
    "phone": "screen time",
    "computer": "screen time",
    "noise": "loud noise",
}


def normalize_triggers(potential_triggers: list) -> list:
    if not isinstance(potential_triggers, list):
        return []

    normalized: list[str] = []
    seen: set[str] = set()
    canonical_lookup = {name.lower(): name for name in CANONICAL_TRIGGER_LIST}

    for trigger in potential_triggers:
        if not isinstance(trigger, str):
            continue
        raw = trigger.strip()
        if not raw:
            continue

        lower = raw.lower()
        canonical = TRIGGER_ALIAS_TO_CANONICAL.get(lower)

        if canonical is None and lower in canonical_lookup:
            canonical = canonical_lookup[lower]

        if canonical is None:
            for alias, mapped in TRIGGER_ALIAS_TO_CANONICAL.items():
                if alias in lower or lower in alias:
                    canonical = mapped
                    break

        if canonical is None:
            canonical = raw

        if canonical not in seen:
            seen.add(canonical)
            normalized.append(canonical)

    return normalized

# --- HELPER FUNCTIONS ---

def call_llm(payload: dict):
    """Handles communicating with the LLM via the Cloudflare tunnel."""
    # ⚠️ DO NOT CHANGE THIS URL UNDER ANY CIRCUMSTANCE - Production LLM endpoint
    llm_base = os.getenv("LLM_SERVER_URL", "https://llm.flairup.dpdns.org").rstrip('/')
    llm_endpoint = f"{llm_base}/generate"
    logger.info("Calling LLM endpoint: %s", llm_endpoint)
    try:
        # Timeout for smaller models (1.7B-4B are ~10-30s, 8B+ can take 30-90s)
        resp = requests.post(llm_endpoint, json=payload, timeout=60)
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
    """Call LLM with chat messages for conversational guided log using OpenAI client."""
    from openai import OpenAI
    
    # ⚠️ DO NOT CHANGE THIS URL UNDER ANY CIRCUMSTANCE - Production LLM endpoint
    llm_base = os.getenv("LLM_SERVER_URL", "https://llm.flairup.dpdns.org").rstrip('/')
    model = os.getenv("LLM_MODEL", "Qwen3-1.7B-Hybrid")
    default_model = "Qwen3-1.7B-Hybrid"
    
    # For OpenAI-compatible API, append /v1 to base URL
    openai_base_url = f"{llm_base}/v1"
    
    logger.info("Calling LLM chat with OpenAI client at: %s with model: %s", openai_base_url, model)
    
    try:
        client = OpenAI(
            api_key="not-needed",
            base_url=openai_base_url
        )
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        # If model not found, retry with default model
        if "model_not_found" in str(e).lower() and model != default_model:
            logger.warning(f"Model '{model}' not found on Lemonade server, retrying with '{default_model}'")
            try:
                response = client.chat.completions.create(
                    model=default_model,
                    messages=messages,
                    temperature=temperature
                )
                return response.choices[0].message.content.strip()
            except Exception as retry_e:
                logger.error("Retry with default model failed: %s", retry_e)
                raise HTTPException(status_code=502, detail=f"LLM chat service unavailable: {str(retry_e)}")
        logger.error("LLM chat request failed: %s", e)
        raise HTTPException(status_code=502, detail=f"LLM chat service unavailable: {str(e)}")


def sanitize_llm_data(llm_data: dict) -> dict:
    """Fix common LLM output issues to pass validation and database constraints.
    
    - Converts severity=0 to severity=5 (mild default)
    - Ensures severity is in range 1-10
    - Ensures required fields exist with proper types
    """
    sanitized = llm_data.copy()
    
    # Fix severity: must be 1-10 for database constraint
    severity = sanitized.get("severity")
    if severity is None or not isinstance(severity, (int, float)):
        sanitized["severity"] = 5  # Default to mild
    elif severity < 1:
        sanitized["severity"] = 1  # Minimum severity
    elif severity > 10:
        sanitized["severity"] = 10  # Maximum severity
    else:
        sanitized["severity"] = int(severity)
    
    # Ensure required arrays exist
    if not isinstance(sanitized.get("symptoms"), list):
        sanitized["symptoms"] = []
    if not isinstance(sanitized.get("potential_triggers"), list):
        sanitized["potential_triggers"] = []
    
    return sanitized


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
        
        # Handle severity: must be 1-10 or NULL (0 becomes NULL)
        severity = llm_data.get("severity")
        if severity is not None and (severity < 1 or severity > 10):
            severity = None
            
        # -- TAXONOMY PIPELINE --
        mapped_triggers = []
        raw_triggers = llm_data.get("potential_triggers", [])
        if raw_triggers:
            from openai import OpenAI
            import os
            
            for trig in raw_triggers:
                trig = str(trig).strip().lower()
                if not trig:
                    continue
                
                # Check DB for existing mapping
                existing_tax = db.query(TriggerTaxonomy).filter(
                    TriggerTaxonomy.user_id == user_id, 
                    TriggerTaxonomy.raw_trigger == trig
                ).first()
                
                if existing_tax:
                    if existing_tax.root_cause not in mapped_triggers:
                        mapped_triggers.append(existing_tax.root_cause)
                else:
                    # Fast secondary LLM call to classify
                    try:
                        llm_base = os.getenv("LLM_SERVER_URL", "https://llm.flairup.dpdns.org").rstrip('/')
                        client = OpenAI(api_key="not-needed", base_url=f"{llm_base}/v1")
                        
                        sys_prompt = (
                            "You classify a raw action string into a 1-3 word broad root cause category.\\n"
                            "Examples:\\n"
                            "'Ate a large pizza' -> 'Heavy Meal'\\n"
                            "'Drank 2 monsters' -> 'Caffeine'\\n"
                            "'Stayed up till 4am' -> 'Sleep Deprivation'\\n"
                            "'Stuck in traffic for 2 hours' -> 'Stress'\\n"
                            "Return ONLY the root cause text."
                        )
                        
                        response = client.chat.completions.create(
                            model=os.getenv("FAST_LLM_MODEL", "AMD-OLMo-1B"),
                            messages=[
                                {"role": "system", "content": sys_prompt},
                                {"role": "user", "content": f"Classify this trigger: {trig}"}
                            ],
                            temperature=0.1,
                            max_tokens=10
                        )
                        
                        root_cause = response.choices[0].message.content.strip().title()
                        
                        # Save mapping
                        new_tax = TriggerTaxonomy(user_id=user_id, raw_trigger=trig, root_cause=root_cause)
                        db.add(new_tax)
                        db.commit()
                        
                        if root_cause not in mapped_triggers:
                            mapped_triggers.append(root_cause)
                    except Exception as llm_err:
                        logger.error("Failed taxonomy LLM call for '%s': %s", trig, llm_err)
                        # Fallback to the original raw trigger
                        if trig not in mapped_triggers:
                            mapped_triggers.append(trig)
            
            # Use mapped triggers for the entry
            llm_data["potential_triggers"] = mapped_triggers
        
        entry = Entry(
            user_id=user_id,
            raw_transcript=transcript,
            symptoms=llm_data.get("symptoms"),
            severity=severity,
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
    Extract structured health data from the following user log.

    Requirements:
    - Identify and list all symptoms mentioned.
    - Identify and list the underlying/root cause(s) or potential triggers for each symptom (e.g., if the user drank coffee, return "caffeine" as the trigger, not just "coffee").
    - Extract severity (1-10), time context, mood, body location, and any relevant notes if present.
    - Return a JSON object with these fields: symptoms (list), severity (integer 1-10), potential_triggers (list), time_context (string), mood (string), body_location (list), notes (string).
    - Only include fields that are present or can be reasonably inferred.

    Example:
    User log: "I have a headache and I drank coffee earlier."
    Return:
    {
        "symptoms": ["headache"],
        "severity": 5,
        "potential_triggers": ["caffeine"],
        "time_context": "",
        "mood": "",
        "body_location": [],
        "notes": ""
    }

    Focus on extracting the most fundamental triggers, not just surface-level causes.
    """
    try:
        body = await request.json()
        user_id = normalize_user_id(body.get("user_id"))
        transcript = body.get("transcript")

        if not transcript:
            raise HTTPException(status_code=400, detail="Missing transcript")

        llm_payload = {
            **body,
            "trigger_reference": CANONICAL_TRIGGER_LIST,
            "extraction_rules": (
                "Extract root-cause triggers and prefer canonical trigger names from trigger_reference. "
                "If user says coffee/tea/energy drink map to caffeine; "
                "stressful situation maps to stress."
            ),
        }
        llm_json = call_llm(llm_payload)
        
        # Sanitize LLM output to fix common issues (e.g., severity=0)
        llm_json = sanitize_llm_data(llm_json)
        llm_json["potential_triggers"] = normalize_triggers(llm_json.get("potential_triggers", []))

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

@app.post("/api/guided-log/start")
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
            "You are a health assistant. Your first question must ask about pain severity on a 1-10 scale.\n\n"
            "Example: 'On a scale of 1-10, how severe is your pain?'\n\n"
            "Keep it under 15 words. Do NOT output JSON or any other format."
        )
        
        # Initialize conversation
        guided_sessions[session_id] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Initial log: {transcript}"}
        ]
        
        # Get first question from LLM
        assistant_message = call_llm_chat(guided_sessions[session_id], temperature=0.3)
        guided_sessions[session_id].append({"role": "assistant", "content": assistant_message})
        
        # Detect broken LLM outputs (thinking tags, XML tags, etc.)
        is_broken = ("<think>" in assistant_message.lower() or 
                    assistant_message.strip().startswith("<") and 
                    not assistant_message.strip().startswith("<?") and
                    ">" in assistant_message[:50])  # Has closing bracket early = likely tag
        if is_broken:
            logger.warning("LLM returned broken output with tags, using default question")
            assistant_message = "On a scale of 1-10, how severe is your pain or discomfort?"
            guided_sessions[session_id][-1] = {"role": "assistant", "content": assistant_message}
        
        # Enforce at least one follow-up question before completion
        user_message_count = sum(1 for msg in guided_sessions[session_id] if msg["role"] == "user")
        
        # Detect if LLM is trying to output JSON without COMPLETE: prefix
        is_raw_json = (assistant_message.strip().startswith('{') and 
                      ('"symptoms"' in assistant_message or '"severity"' in assistant_message))
        
        # Check if COMPLETE appears anywhere or if it's raw JSON (handle malformed responses)
        if (("COMPLETE" in assistant_message.upper()) or is_raw_json) and user_message_count < 3:
            # LLM tried to complete too early, force a question instead
            logger.warning("LLM tried to complete without asking questions, forcing follow-up")
            assistant_message = "On a scale of 1-10, how severe is your pain or discomfort?"
            guided_sessions[session_id][-1] = {"role": "assistant", "content": assistant_message}
        
        # Check if complete (should only happen if NOT first response)
        if "COMPLETE:" in assistant_message or "COMPLETE{" in assistant_message:
            extracted_data = _extract_completion_data(assistant_message)
            # Keep session for /finalize endpoint - will be deleted there
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


@app.post("/api/guided-log/respond")
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
        
        # Update system prompt after first answer to focus on triggers
        user_message_count = sum(1 for msg in guided_sessions[session_id] if msg["role"] == "user")
        if user_message_count == 2:  # Just got second user message (initial + first answer)
            # After severity, ask about triggers
            guided_sessions[session_id][0]["content"] = (
                "You are a helpful health assistant. Ask one focused follow-up to find ROOT cause triggers.\\n\\n"
                f"Prefer these canonical trigger categories: {', '.join(CANONICAL_TRIGGER_LIST)}\\n\\n"
                "Ask about ONE area only (food/drink, stress-emotion, environment, activity/injury, sleep).\\n"
                "Keep the question under 15 words."
            )
        elif user_message_count == 3:  # Got trigger answer, now allow completion
            guided_sessions[session_id][0]["content"] = (
                "You are a helpful health assistant. You have enough information now.\\n\\n"
                "Respond with EXACTLY this format (no extra text):\\n"
                'COMPLETE:{"symptoms": ["symptom"], "severity": 5, "potential_triggers": ["trigger"], '
                '"mood": "string", "body_location": ["location"], "time_context": "string", "notes": "string"}\\n\\n'
                f"Use canonical triggers where possible: {', '.join(CANONICAL_TRIGGER_LIST)}.\\n"
                "Map similar phrases to basic forms (e.g., stressful experience -> stress, coffee -> caffeine).\\n"
                "Use the actual data from the conversation. Include the word COMPLETE: at the start."
            )
        
        # Get next question or completion from LLM
        assistant_message = call_llm_chat(guided_sessions[session_id], temperature=0.5)
        guided_sessions[session_id].append({"role": "assistant", "content": assistant_message})
        
        # After 4+ user messages, force completion regardless of LLM output
        if user_message_count >= 4:
            logger.info(f"Reached {user_message_count} user messages, forcing completion")
            # Extract data from conversation using /generate endpoint
            conversation = guided_sessions[session_id]
            transcript_parts = []
            for msg in conversation:
                if msg["role"] == "user":
                    transcript_parts.append(f"User: {msg['content']}")
                elif msg["role"] == "assistant" and not msg["content"].startswith("COMPLETE"):
                    transcript_parts.append(f"Assistant: {msg['content']}")
            
            full_transcript = "\\n".join(transcript_parts)
            
            try:
                extracted_data = call_llm({
                    "user_id": body.get("user_id", "00000000-0000-0000-0000-000000000001"),
                    "transcript": f"Conversation:\\n{full_transcript}\\n\\nExtract the symptom data.",
                    "trigger_reference": CANONICAL_TRIGGER_LIST,
                    "extraction_rules": "Prefer canonical triggers from trigger_reference and map similar phrases to root-cause names.",
                })
                extracted_data = sanitize_llm_data(extracted_data)
                extracted_data["potential_triggers"] = normalize_triggers(extracted_data.get("potential_triggers", []))
                
                return {
                    "session_id": session_id,
                    "question": None,
                    "is_complete": True,
                    "extracted_data": extracted_data
                }
            except Exception as e:
                logger.error(f"Failed to force completion: {e}")
                # Continue to normal flow
        
        # Detect broken LLM outputs (thinking tags, XML tags, etc.)
        is_broken = ("<think>" in assistant_message.lower() or 
                    (assistant_message.strip().startswith("<") and 
                     not assistant_message.strip().startswith("<?") and
                     ">" in assistant_message[:50]))  # Has closing bracket early = likely tag
        
        # If broken after 3rd user message, force completion instead of asking again
        if is_broken and user_message_count >= 3:
            logger.warning("LLM returned broken output after 3 questions, forcing completion")
            # Use /generate to extract from conversation
            conversation = guided_sessions[session_id]
            transcript_parts = []
            for msg in conversation:
                if msg["role"] == "user":
                    transcript_parts.append(f"User: {msg['content']}")
                elif msg["role"] == "assistant" and not msg["content"].startswith("COMPLETE"):
                    transcript_parts.append(f"Assistant: {msg['content']}")
            
            full_transcript = "\\n".join(transcript_parts)
            
            try:
                extracted_data = call_llm({
                    "user_id": body.get("user_id", "00000000-0000-0000-0000-000000000001"),
                    "transcript": f"Conversation:\\n{full_transcript}\\n\\nExtract the symptom data.",
                    "trigger_reference": CANONICAL_TRIGGER_LIST,
                    "extraction_rules": "Prefer canonical triggers from trigger_reference and map similar phrases to root-cause names.",
                })
                extracted_data = sanitize_llm_data(extracted_data)
                extracted_data["potential_triggers"] = normalize_triggers(extracted_data.get("potential_triggers", []))
                
                return {
                    "session_id": session_id,
                    "question": None,
                    "is_complete": True,
                    "extracted_data": extracted_data
                }
            except Exception as e:
                logger.error(f"Failed to force completion: {e}")
                # Continue to normal flow
        
        if is_broken:
            logger.warning("LLM returned broken output with tags, using default question")
            # Determine which question to ask based on user count
            if user_message_count == 2:
                assistant_message = "What do you think might have caused this? Any activities, injuries, foods, or stress?"
            else:
                assistant_message = "Can you tell me when this started?"
            guided_sessions[session_id][-1] = {"role": "assistant", "content": assistant_message}
        
        # Enforce at least 3 user messages (initial + 2 answers) before allowing completion
        user_message_count = sum(1 for msg in guided_sessions[session_id] if msg["role"] == "user")
        
        # Detect if LLM is trying to output JSON without COMPLETE: prefix
        is_raw_json = (assistant_message.strip().startswith('{') and 
                      ('"symptoms"' in assistant_message or '"severity"' in assistant_message))
        
        # Check if COMPLETE appears anywhere or if it's raw JSON
        if (("COMPLETE" in assistant_message.upper()) or is_raw_json) and user_message_count < 3:
            # Force another question if too early
            logger.warning(f"LLM tried to complete too early (user_count={user_message_count}), forcing trigger question")
            if user_message_count == 2:
                assistant_message = "What do you think might have caused this? Any activities, injuries, foods, or situations before you noticed it?"
            else:
                assistant_message = "Can you tell me more about what might have triggered this?"
            guided_sessions[session_id][-1] = {"role": "assistant", "content": assistant_message}
        
        # Check if complete
        if "COMPLETE:" in assistant_message or "COMPLETE{" in assistant_message:
            extracted_data = _extract_completion_data(assistant_message)
            # Keep session for /finalize endpoint - will be deleted there
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
        # Find the JSON object in the message
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
        
        # Find the actual JSON object - extract from first { to last }
        first_brace = json_str.find('{')
        last_brace = json_str.rfind('}')
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            json_str = json_str[first_brace:last_brace+1]
        else:
            # No valid JSON braces found
            logger.error(f"No JSON braces found in: {completion_message}")
            raise HTTPException(status_code=502, detail="LLM returned incomplete data - please try again")
        
        # Check if it's just the placeholder text
        if json_str.strip() in ['{json_object}', '{...}']:
            logger.error(f"LLM returned placeholder instead of data: {completion_message}")
            raise HTTPException(status_code=502, detail="LLM returned placeholder - please try again")
        
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse completion JSON: {completion_message}")
        logger.error(f"Extracted string was: {json_str if 'json_str' in locals() else 'N/A'}")
        raise HTTPException(status_code=500, detail="Failed to parse completion data")


def _finalize_guided_session(session_id: str, user_id: str) -> dict:
    """Finalize a guided session by sending conversation to /generate endpoint."""
    if session_id not in guided_sessions:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    conversation = guided_sessions[session_id]
    
    # Extract conversation text for transcript
    transcript_parts = []
    for msg in conversation:
        if msg["role"] == "user":
            transcript_parts.append(f"User: {msg['content']}")
        elif msg["role"] == "assistant":
            transcript_parts.append(f"Assistant: {msg['content']}")
    
    full_transcript = "\n".join(transcript_parts)
    
    # Call /generate endpoint with the full conversation
    try:
        llm_data = call_llm({
            "user_id": user_id,
            "transcript": f"Conversation:\n{full_transcript}\n\nExtract the final symptom data from this conversation.",
            "trigger_reference": CANONICAL_TRIGGER_LIST,
            "extraction_rules": "Prefer canonical triggers from trigger_reference and map similar phrases to root-cause names.",
        })
        
        # Sanitize LLM output to fix common issues (e.g., severity=0)
        llm_data = sanitize_llm_data(llm_data)
        llm_data["potential_triggers"] = normalize_triggers(llm_data.get("potential_triggers", []))
        
        # Validate the extracted data
        is_valid, error_msg = validate_voicehealth_json_py(json.dumps(llm_data))
        if not is_valid:
            logger.error("Final LLM output failed validation: %s", error_msg)
            raise HTTPException(status_code=422, detail=f"LLM returned invalid data: {error_msg}")
        
        del guided_sessions[session_id]  # Clean up
        return llm_data
        
    except Exception as e:
        logger.error("Failed to finalize guided session: %s", e)
        raise HTTPException(status_code=502, detail=f"Finalization failed: {str(e)}")


@app.post("/api/guided-log/finalize")
async def guided_log_finalize(request: Request):
    """Finalize a guided session: converts conversation to structured symptom data.
    
    Sends the full conversation to /generate endpoint to extract final JSON.
    """
    try:
        body = await request.json()
        session_id = body.get("session_id")
        user_id = body.get("user_id") or "00000000-0000-0000-0000-000000000001"
        
        if not session_id:
            raise HTTPException(status_code=400, detail="Missing session_id")
        
        extracted_data = _finalize_guided_session(session_id, user_id)
        
        # Save to database
        entry_id = save_entry_to_db(user_id, "", extracted_data)
        
        return {
            "session_id": session_id,
            "extracted_data": extracted_data,
            "entry_id": entry_id,
            "status": "completed"
        }
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Guided log finalize failed: %s\n%s", exc, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Finalization failed: {str(exc)}")


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
    
    # 2. Sanitize LLM output to fix common issues (e.g., severity=0)
    llm_json = sanitize_llm_data(llm_json)
    llm_json["potential_triggers"] = normalize_triggers(llm_json.get("potential_triggers", []))

    # 3. Validate the final extraction
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
        
        # Build a summary transcript for the LLM
        transcript_summary = f"User health summary: {current_entry_count} total entries. "
        transcript_summary += f"Average severity: {round(avg_severity, 1)}/10. "
        if top_symptoms:
            transcript_summary += f"Most common symptoms: {', '.join([s[0] for s in top_symptoms[:3]])}. "
        if recent_entries and recent_entries[0].raw_transcript:
            transcript_summary += f"Latest entry: {recent_entries[0].raw_transcript}"
        
        llm_payload = {
            "mode": "generate_insights",
            "user_id": user_id,
            "transcript": transcript_summary,  # Required field for /generate endpoint
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
    """Fetch all history entries for a user."""
    db = SessionLocal()
    try:
        entries = db.query(Entry).filter(Entry.user_id == user_id).order_by(Entry.logged_at.desc()).all()
        
        # Serialize the SQLAlchemy objects into dictionaries
        entry_list = []
        for e in entries:
            entry_list.append({
                "id": str(e.id),
                "raw_transcript": e.raw_transcript,
                "symptoms": e.symptoms if e.symptoms else [],
                "severity": e.severity,
                "potential_triggers": e.potential_triggers if e.potential_triggers else [],
                "notes": e.notes,
                "logged_at": e.logged_at.isoformat() if e.logged_at else None
            })

        return {
            "status": "success",
            "user_id": user_id,
            "entries": entry_list
        }
    except Exception as e:
        logger.error(f"Error getting history: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.put("/api/entries/{entry_id}")
async def update_entry(entry_id: str, request: Request):
    """Update an existing log entry."""
    db = SessionLocal()
    try:
        update_data = await request.json()
        entry = db.query(Entry).filter(Entry.id == entry_id).first()
        
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")

        # Update allowed fields
        if "symptoms" in update_data:
            entry.symptoms = update_data["symptoms"]
        if "potential_triggers" in update_data:
            entry.potential_triggers = update_data["potential_triggers"]
        if "notes" in update_data:
            entry.notes = update_data["notes"]
        if "severity" in update_data:
            sev = update_data["severity"]
            # Enforce constraints
            if sev is None or (isinstance(sev, int) and 1 <= sev <= 10):
                entry.severity = sev

        db.commit()
        return {"status": "success", "message": "Entry updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating entry {entry_id}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

if __name__ == "__main__":
    # ⚠️ DO NOT CHANGE PORT 8000 UNDER ANY CIRCUMSTANCE - Container internal port
    uvicorn.run(app, host="0.0.0.0", port=8000)