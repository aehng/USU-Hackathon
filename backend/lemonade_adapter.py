from fastapi import FastAPI, Request, HTTPException
import uvicorn
import os
import json
from openai import OpenAI
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Lemonade Symptom Extraction Adapter")

# ============================================================================
# PYDANTIC MODELS - Define strict response schema
# ============================================================================

class SymptomExtraction(BaseModel):
    """Schema for extracting symptoms from a single voice/text log entry."""
    symptoms: List[str]  # e.g., ["headache", "nausea", "dizziness"]
    severity: int  # 1-10 scale
    potential_triggers: List[str]  # e.g., ["stress", "caffeine", "lack of sleep"]
    mood: Optional[str] = None  # e.g., "anxious", "tired", "fine"
    body_location: Optional[str] = None  # e.g., "head", "stomach", "chest"
    time_context: Optional[str] = None  # e.g., "since morning", "for 2 hours", "all day"
    notes: Optional[str] = None  # Any additional context

# ============================================================================
# CONFIGURATION
# ============================================================================

LEMONADE_BASE = os.getenv("LEMONADE_BASE_URL", "http://localhost:8080")
MODEL = os.getenv("LLM_MODEL", "qwen-3-hybrid")
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

    # System prompt for symptom extraction
    system_prompt = (
        "You are a medical symptom extraction assistant. Extract health information "
        "from the user's description. Be precise and conservative - only extract "
        "information explicitly stated. Return severity as an integer 1-10."
    )
    
    user_content = (
        f"Extract symptoms, severity, triggers, mood, body location, time context, "
        f"and any other relevant notes from this description:\n\n{transcript}"
    )

    try:
        # Use .parse() for strict schema validation
        print(f"🔄 Sending request to Lemonade at {LEMONADE_BASE} with model {MODEL}")
        response = client.beta.chat.completions.parse(
            model=MODEL,
            response_format=SymptomExtraction,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.0,
        )
        
        # .parsed returns the validated Pydantic object
        parsed_obj = response.choices[0].message.parsed
        print(f"✅ Successfully extracted symptoms: {parsed_obj.symptoms}")
        return json.loads(parsed_obj.model_dump_json())

    except Exception as exc:
        print(f"❌ LLM extraction error: {type(exc).__name__}: {str(exc)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=502,
            detail=f"LLM extraction failed: {str(exc)}"
        )


if __name__ == "__main__":
    # Default adapter port is 8000 on the laptop
    port = int(os.getenv("ADAPTER_PORT", "8000"))
    uvicorn.run("lemonade_adapter:app", host="0.0.0.0", port=port, log_level="info")
