from fastapi import FastAPI, Request, HTTPException
import uvicorn
import os
import json
from openai import OpenAI
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Lemonade Adapter with Strict JSON Validation")

# ============================================================================
# PYDANTIC MODELS - Define strict response schema
# ============================================================================

class TriggerCorrelation(BaseModel):
    name: str
    value: int

class TemporalPattern(BaseModel):
    symptom: str
    peak_day: Optional[str]
    peak_time: str
    frequency: int

class SeverityTrend(BaseModel):
    date: str
    severity: float

class SymptomFrequency(BaseModel):
    name: str
    value: int

class HealthTrackingData(BaseModel):
    trigger_correlations: List[TriggerCorrelation]
    temporal_patterns: List[TemporalPattern]
    severity_trends: List[SeverityTrend]
    symptom_frequency: List[SymptomFrequency]
    total_entries: int
    date_range_days: int

# ============================================================================
# CONFIGURATION
# ============================================================================

LEMONADE_BASE = os.getenv("LEMONADE_BASE_URL", "http://localhost:8000")
MODEL = os.getenv("LLM_MODEL", "qwen-3-hybrid")
API_KEY = os.getenv("OPENAI_API_KEY", "not-needed-for-local")

# Initialize OpenAI client pointing to local Lemonade server
client = OpenAI(
    api_key=API_KEY,
    base_url=LEMONADE_BASE.rstrip("/")
)


@app.post("/generate")
async def generate(request: Request):
    """Forward requests to Lemonade using OpenAI .parse() for strict JSON schema.

    Expected input JSON:
      { "input": <data>, "prompt": "optional prompt" }

    Uses Pydantic models to enforce strict response validation. The LLM must
    produce JSON that matches the HealthTrackingData schema exactly.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid json body")

    # Extract fields
    input_data = None
    prompt = (
        "You are a precise data extraction engine. Analyze the user's input "
        "and extract the required health tracking metrics exactly as defined. "
        "Ensure all dates are in YYYY-MM-DD format."
    )
    if isinstance(payload, dict):
        input_data = payload.get("input", payload)
        prompt = payload.get("prompt", prompt)
    else:
        input_data = payload

    # Serialize input data
    try:
        data_blob = json.dumps(input_data)
    except Exception:
        data_blob = str(input_data)

    user_content = f"{prompt}\n\nDATA:\n{data_blob}"

    try:
        # Use .parse() for strict schema validation
        response = client.beta.chat.completions.parse(
            model=MODEL,
            response_format=HealthTrackingData,
            messages=[
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": user_content
                }
            ],
            temperature=0.0,
        )
        # .parsed returns the validated Pydantic object
        parsed_obj = response.choices[0].message.parsed
        return json.loads(parsed_obj.model_dump_json())

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Lemonade parse request failed: {str(exc)}"
        )


if __name__ == "__main__":
    # Default adapter port is 8000 on the laptop
    port = int(os.getenv("ADAPTER_PORT", "8000"))
    uvicorn.run("lemonade_adapter:app", host="0.0.0.0", port=port, log_level="info")
