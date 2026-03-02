from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
import uvicorn
import os
import json
import logging
import tempfile
import shutil
import requests as http_requests
from openai import OpenAI
from pydantic import BaseModel
from typing import List, Optional
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

app = FastAPI(title="Lemonade Symptom Extraction Adapter")

# Hardcoded canonical trigger vocabulary (temporary; can be replaced with DB lookup later)
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

# ============================================================================
# PYDANTIC MODELS - Define strict response schema
# ============================================================================

class SymptomExtraction(BaseModel):
    """Schema for extracting symptoms from a single voice/text log entry."""
    symptoms: List[str]  # e.g., ["headache", "nausea", "dizziness"]
    severity: int  # 1-10 scale
    potential_triggers: Optional[List[str]] = []  # e.g., ["stress", "caffeine", "lack of sleep"]
    mood: Optional[str] = None  # e.g., "anxious", "tired", "fine"
    body_location: Optional[List[str]] = None  # e.g., ["head"], ["stomach", "chest"]
    time_context: Optional[str] = None  # e.g., "since morning", "for 2 hours", "all day"
    notes: Optional[str] = None  # Any additional context

# ============================================================================
# CONFIGURATION
# ============================================================================

LEMONADE_BASE = os.getenv("LEMONADE_BASE_URL", "http://localhost:8080/v1")
# Derive the Lemonade server root (strip /v1 suffix if present)
LEMONADE_ROOT = LEMONADE_BASE.rstrip("/")
if LEMONADE_ROOT.endswith("/v1"):
    LEMONADE_ROOT = LEMONADE_ROOT[:-3]
# Use a model that exists in Lemonade. Common options:
# - Qwen3-1.7B-Hybrid (very fast, decent quality - RECOMMENDED FOR DEMOS)
# - Qwen3-4B-Hybrid (medium speed, good quality)
# - CodeLlama-7b-Instruct-hf-Hybrid (medium, code-focused)
# - Qwen3-8B-Hybrid (larger, more capable but slower)
# Run: GET http://localhost:8080/api/v1/models?show_all=true to see all models
MODEL = os.getenv("LLM_MODEL", "Qwen3-1.7B-Hybrid")
API_KEY = os.getenv("OPENAI_API_KEY", "not-needed-for-local")

# Initialize OpenAI client pointing to local Lemonade server
client = OpenAI(
    api_key=API_KEY,
    base_url=LEMONADE_BASE.rstrip("/")
)

print(f"🚀 Lemonade Adapter starting...")
print(f"   Lemonade URL: {LEMONADE_BASE}")
print(f"   Model: {MODEL}")
print(f"   Attempting to connect to Lemonade...")

# Initialize Whisper model for audio transcription
print(f"🎤 Loading Faster-Whisper model...")
# Use "base" for speed, "small" for better quality, "medium" for even better (but slower)
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")
whisper_model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
print(f"✅ Whisper model loaded ({WHISPER_MODEL_SIZE})")


@app.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe audio file to text using Faster-Whisper.
    
    Accepts: audio file (webm, ogg, mp3, wav, etc.)
    Returns: { "text": "transcribed text here" }
    """
    print(f"🎤 Received audio file: {audio.filename}, content_type: {audio.content_type}")
    
    # Create temporary file to save uploaded audio
    temp_audio = None
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
            temp_audio = temp_file.name
            shutil.copyfileobj(audio.file, temp_file)
        
        print(f"📁 Saved audio to: {temp_audio}")
        print(f"🔄 Transcribing with Whisper...")
        
        # Transcribe using Faster-Whisper
        segments, info = whisper_model.transcribe(
            temp_audio,
            language="en",  # Force English for faster processing
            beam_size=1,    # Faster, slightly less accurate
            vad_filter=True  # Filter out silence/noise
        )
        
        # Collect all segments into a single transcript
        transcript = " ".join([segment.text.strip() for segment in segments])
        
        print(f"✅ Transcription complete: {transcript[:100]}...")
        
        return {"text": transcript}
        
    except Exception as e:
        print(f"❌ Transcription error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Transcription failed: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if temp_audio and os.path.exists(temp_audio):
            try:
                os.unlink(temp_audio)
            except Exception:
                pass


@app.post("/generate")
async def generate(request: Request):
    """Extract symptoms from voice/text transcript using LLM.

    Expected input JSON:
      { 
        "input": {
          "user_id": "demo-user-001",
          "transcript": "I've had a terrible headache since this morning..."
        }
      }

    Returns extracted symptom data matching the Entry model schema.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid json body")

    # Extract transcript from nested input structure
    input_data = payload.get("input", {})
    transcript = input_data.get("transcript", "")
    trigger_reference = input_data.get("trigger_reference") or CANONICAL_TRIGGER_LIST
    
    if not transcript:
        raise HTTPException(status_code=400, detail="transcript field is required")

    # System prompt for symptom extraction with explicit JSON formatting
    system_prompt = (
        "You are a medical symptom extraction assistant. ALWAYS extract health information from the user's description. "
        "IMPORTANT: You MUST identify and return at least ONE symptom if the user mentions any physical or health issue.\n\n"
        "Rules:\n"
        "1. ALWAYS extract mentioned symptoms (e.g., 'my head hurts' -> ['headache']\n"
        "2. Extract severity as 1-10 integer. If mentioned, use that number. Default to 5.\n"
        "3. For potential_triggers, use canonical names from: "
        f"{', '.join(trigger_reference)}\n"
        "4. If user says a synonym, map to canonical term (e.g., 'coffee' -> 'caffeine')\n"
        "5. body_location should be specific if mentioned (e.g., ['foot', 'lower leg'])\n"
        "6. Return ONLY valid JSON with no markdown formatting:\n"
        "{\n"
        '  "symptoms": ["symptom1"],\n'
        '  "severity": integer,\n'
        '  "potential_triggers": ["trigger1"],\n'
        '  "body_location": ["location"] or null,\n'
        '  "mood": "string" or null,\n'
        '  "time_context": "string" or null,\n'
        '  "notes": "string" or null\n'
        "}"
    )
    
    user_content = f"Extract symptoms from this description:\n\n{transcript}"

    try:
        # Use regular completion (not .parse()) since Lemonade returns text
        print(f"🔄 Sending request to Lemonade at {LEMONADE_BASE} with model {MODEL}")
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.2,
        )
        
        # Extract the text response
        llm_text = response.choices[0].message.content.strip()
        print(f"📥 LLM response: {llm_text[:200]}...")
        
        # Try to parse JSON from the response
        # Remove markdown code blocks if present
        if llm_text.startswith("```"):
            # Extract JSON from markdown code block
            lines = llm_text.split("\n")
            json_lines = []
            in_code_block = False
            for line in lines:
                if line.startswith("```"):
                    in_code_block = not in_code_block
                elif in_code_block:
                    json_lines.append(line)
            llm_text = "\n".join(json_lines).strip()
        
        # Parse the JSON
        try:
            parsed_data = json.loads(llm_text)
        except json.JSONDecodeError:
            # If still failing, try to extract JSON from anywhere in the text
            import re
            json_match = re.search(r'\{[^{}]*"symptoms"[^{}]*\}', llm_text, re.DOTALL)
            if json_match:
                parsed_data = json.loads(json_match.group())
            else:
                raise ValueError(f"Could not parse JSON from LLM response: {llm_text[:200]}")
        
        # Validate against Pydantic model
        validated = SymptomExtraction(**parsed_data)
        print(f"✅ Successfully extracted symptoms: {validated.symptoms}")
        return validated.model_dump()

    except Exception as exc:
        print(f"❌ LLM extraction error: {type(exc).__name__}: {str(exc)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=502,
            detail=f"LLM extraction failed: {str(exc)}"
        )


@app.post("/chat")
async def chat(request: Request):
    """Conversational chat endpoint for guided logging.
    
    Expected input JSON:
      {
        "messages": [
          {"role": "system", "content": "..."},
          {"role": "user", "content": "..."},
          {"role": "assistant", "content": "..."}
        ],
        "temperature": 0.7
      }
    
    Returns: { "response": "assistant's reply" }
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid json body")
    
    messages = payload.get("messages", [])
    temperature = payload.get("temperature", 0.7)
    
    if not messages:
        raise HTTPException(status_code=400, detail="messages field is required")
    
    try:
        print(f"🔄 Sending chat request to Lemonade at {LEMONADE_BASE} with model {MODEL}")
        print(f"📝 Message count: {len(messages)}")
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=temperature
        )
        
        assistant_response = response.choices[0].message.content.strip()
        print(f"✅ Chat response: {assistant_response[:100]}...")
        
        return {"response": assistant_response}
        
    except Exception as exc:
        print(f"❌ Chat error: {type(exc).__name__}: {str(exc)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=502,
            detail=f"Chat failed: {str(exc)}"
        )


@app.post("/v1/chat/completions")
async def openai_chat_completions(request: Request):
    """OpenAI-compatible chat completions endpoint.
    
    Expected input JSON (OpenAI format):
      {
        "model": "model-name",
        "messages": [
          {"role": "system", "content": "..."},
          {"role": "user", "content": "..."}
        ],
        "temperature": 0.7
      }
    
    Returns OpenAI-compatible response format.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid json body")
    
    messages = payload.get("messages", [])
    temperature = payload.get("temperature", 0.7)
    model = payload.get("model", MODEL)
    default_model = "Qwen3-1.7B-Hybrid"
    
    if not messages:
        raise HTTPException(status_code=400, detail="messages field is required")
    
    try:
        print(f"🔄 OpenAI API: Sending chat request to Lemonade at {LEMONADE_BASE} with model {model}")
        print(f"📝 Message count: {len(messages)}")
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        
        # Return the OpenAI response directly (it's already in the right format)
        print(f"✅ OpenAI API response generated")
        return response.model_dump()
        
    except Exception as exc:
        # If model not found, retry with default model
        if "model_not_found" in str(exc).lower() and model != default_model:
            print(f"⚠️  Model '{model}' not found, retrying with default model '{default_model}'")
            try:
                response = client.chat.completions.create(
                    model=default_model,
                    messages=messages,
                    temperature=temperature
                )
                print(f"✅ Retry with default model succeeded")
                return response.model_dump()
            except Exception as retry_exc:
                print(f"❌ Retry also failed: {type(retry_exc).__name__}: {str(retry_exc)}")
                raise HTTPException(
                    status_code=502,
                    detail=f"Chat completions failed: {str(retry_exc)}"
                )
        
        print(f"❌ OpenAI API error: {type(exc).__name__}: {str(exc)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=502,
            detail=f"Chat completions failed: {str(exc)}"
        )




# ============================================================================
# LEMONADE MONITORING ENDPOINTS (proxy to real Lemonade server)
# The Lemonade desktop app polls these endpoints for health/stats/logs.
# We proxy them so requests that land on the adapter port work correctly.
# ============================================================================

@app.get("/api/v1/health")
async def proxy_health():
    """Proxy Lemonade health check to the real Lemonade server."""
    target = f"{LEMONADE_ROOT}/api/v1/health"
    try:
        resp = http_requests.get(target, timeout=5)
        return resp.json()
    except http_requests.RequestException as exc:
        logger.warning("Lemonade health proxy failed: %s", exc)
        return {"status": "unavailable", "message": "Lemonade server not reachable"}


@app.get("/api/v1/stats")
async def proxy_stats():
    """Proxy Lemonade performance stats to the real Lemonade server."""
    target = f"{LEMONADE_ROOT}/api/v1/stats"
    try:
        resp = http_requests.get(target, timeout=5)
        return resp.json()
    except http_requests.RequestException as exc:
        logger.warning("Lemonade stats proxy failed: %s", exc)
        return {"stats": {}, "message": "Lemonade server not reachable"}


@app.get("/api/v1/logs/stream")
async def proxy_logs_stream():
    """Proxy Lemonade SSE log stream from the real Lemonade server."""
    target = f"{LEMONADE_ROOT}/api/v1/logs/stream"

    def event_stream():
        try:
            with http_requests.get(target, stream=True, timeout=60) as resp:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
        except http_requests.RequestException as exc:
            logger.warning("Lemonade log stream proxy failed: %s", exc)
            yield b"data: {\"message\": \"Lemonade server not reachable\"}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    # Default adapter port is 8000 on the laptop
    port = int(os.getenv("ADAPTER_PORT", "8000"))
    uvicorn.run("lemonade_adapter:app", host="0.0.0.0", port=port, log_level="info")
