from fastapi import FastAPI, Request, HTTPException, UploadFile, File
import uvicorn
import os
import json
import tempfile
import shutil
from openai import OpenAI
from pydantic import BaseModel
from typing import List, Optional
from faster_whisper import WhisperModel

app = FastAPI(title="Lemonade Symptom Extraction Adapter")

# ============================================================================
# PYDANTIC MODELS - Define strict response schema
# ============================================================================

class SymptomExtraction(BaseModel):
    """Schema for extracting symptoms from a single voice/text log entry."""
    symptoms: List[str]  # e.g., ["headache", "nausea", "dizziness"]
    severity: int  # 1-10 scale
    potential_triggers: Optional[List[str]] = []  # e.g., ["stress", "caffeine", "lack of sleep"]
    mood: Optional[str] = None  # e.g., "anxious", "tired", "fine"
    body_location: Optional[str] = None  # e.g., "head", "stomach", "chest"
    time_context: Optional[str] = None  # e.g., "since morning", "for 2 hours", "all day"
    notes: Optional[str] = None  # Any additional context

# ============================================================================
# CONFIGURATION
# ============================================================================

LEMONADE_BASE = os.getenv("LEMONADE_BASE_URL", "http://localhost:8080/v1")
# Use a model that exists in Lemonade. Common options:
# - AMD-OLMo-1B-SFT-DPO-Hybrid (fast, small)
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
    
    if not transcript:
        raise HTTPException(status_code=400, detail="transcript field is required")

    # System prompt for symptom extraction with explicit JSON formatting
    system_prompt = (
        "You are a medical symptom extraction assistant. Extract health information, and potential triggers"
        "from the user's description. Be conservative - only extract information explicitly stated. "
        "Return ONLY valid JSON matching this exact format, with no markdown formatting: \n"
        "{\n"
        '  "symptoms": ["symptom1", "symptom2"],\n'
        '  "severity": 5,\n'
        '  "potential_triggers": ["trigger1"],\n'
        '  "mood": "optional string or null",\n'
        '  "body_location": "optional string or null",\n'
        '  "time_context": "optional string or null",\n'
        '  "notes": "optional string or null"\n'
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
        print(f"❌ OpenAI API error: {type(exc).__name__}: {str(exc)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=502,
            detail=f"Chat completions failed: {str(exc)}"
        )


if __name__ == "__main__":
    # Default adapter port is 8000 on the laptop
    port = int(os.getenv("ADAPTER_PORT", "8000"))
    uvicorn.run("lemonade_adapter:app", host="0.0.0.0", port=port, log_level="info")
