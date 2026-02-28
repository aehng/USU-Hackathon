from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
from openai import OpenAI
import json
import uuid

app = FastAPI(title="Guided Log Service")

# ============================================================================
# CONFIGURATION
# ============================================================================

LEMONADE_BASE = os.getenv("LEMONADE_BASE_URL", "http://localhost:8080/v1")
MODEL = os.getenv("LLM_MODEL", "Qwen3-1.7B-Hybrid")
API_KEY = os.getenv("OPENAI_API_KEY", "not-needed-for-local")

client = OpenAI(
    api_key=API_KEY,
    base_url=LEMONADE_BASE.rstrip("/")
)

# In-memory conversation storage (in production, use Redis or similar)
conversations: Dict[str, List[Dict]] = {}

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class StartGuidedLogRequest(BaseModel):
    """Initial request to start guided logging"""
    transcript: str
    user_id: Optional[str] = None

class FollowUpResponse(BaseModel):
    """Response from follow-up question"""
    session_id: str
    answer: str

class GuidedLogState(BaseModel):
    """Current state of the guided log conversation"""
    session_id: str
    question: Optional[str] = None  # Next question to ask user
    is_complete: bool = False
    extracted_data: Optional[Dict] = None  # Final extracted symptoms/data

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.post("/guided-log/start", response_model=GuidedLogState)
async def start_guided_log(request: StartGuidedLogRequest):
    """
    Start a guided log session. Returns first follow-up question.
    
    The LLM will analyze the initial transcript and ask clarifying questions
    to gather more complete symptom information.
    """
    session_id = str(uuid.uuid4())
    
    # Initialize conversation history
    system_prompt = (
        "You are a compassionate health assistant helping someone log their symptoms. "
        "Your goal is to gather complete information through natural conversation. "
        "Based on what the user tells you, ask ONE specific follow-up question at a time to:\n"
        "1. Clarify symptom severity (1-10 scale if not mentioned)\n"
        "2. Identify potential triggers (food, stress, activities, environment)\n"
        "3. Understand timing and duration\n"
        "4. Learn about body location and type of discomfort\n"
        "5. Understand mood and emotional state\n\n"
        "Keep questions short, empathetic, and conversational. "
        "Ask about the MOST important missing information first. "
        "After 2-4 questions, when you have enough information, respond with "
        "EXACTLY this format: 'COMPLETE:{json_object}' where json_object contains:\n"
        '{"symptoms": ["list"], "severity": 5, "potential_triggers": ["list"], '
        '"mood": "string", "body_location": "string", "time_context": "string", "notes": "string"}'
    )
    
    conversations[session_id] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Initial log: {request.transcript}"}
    ]
    
    try:
        # Get first follow-up question from LLM
        response = client.chat.completions.create(
            model=MODEL,
            messages=conversations[session_id],
            temperature=0.7,
        )
        
        assistant_message = response.choices[0].message.content.strip()
        conversations[session_id].append({"role": "assistant", "content": assistant_message})
        
        # Check if LLM thinks it's complete
        if assistant_message.startswith("COMPLETE:"):
            return await _complete_session(session_id, assistant_message)
        
        return GuidedLogState(
            session_id=session_id,
            question=assistant_message,
            is_complete=False
        )
        
    except Exception as e:
        print(f"❌ Error starting guided log: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start guided log: {str(e)}")


@app.post("/guided-log/respond", response_model=GuidedLogState)
async def respond_to_question(response: FollowUpResponse):
    """
    Submit answer to a follow-up question. Returns next question or completion.
    """
    session_id = response.session_id
    
    if session_id not in conversations:
        raise HTTPException(status_code=404, detail="Session not found. It may have expired.")
    
    # Add user's answer to conversation
    conversations[session_id].append({"role": "user", "content": response.answer})
    
    try:
        # Get next question or completion from LLM
        llm_response = client.chat.completions.create(
            model=MODEL,
            messages=conversations[session_id],
            temperature=0.7,
        )
        
        assistant_message = llm_response.choices[0].message.content.strip()
        conversations[session_id].append({"role": "assistant", "content": assistant_message})
        
        # Check if complete
        if assistant_message.startswith("COMPLETE:"):
            return await _complete_session(session_id, assistant_message)
        
        return GuidedLogState(
            session_id=session_id,
            question=assistant_message,
            is_complete=False
        )
        
    except Exception as e:
        print(f"❌ Error in guided log response: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process response: {str(e)}")


async def _complete_session(session_id: str, completion_message: str) -> GuidedLogState:
    """
    Extract final data from completion message and clean up session.
    """
    try:
        # Extract JSON from completion message
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
        
        extracted_data = json.loads(json_str)
        
        # Clean up conversation from memory
        if session_id in conversations:
            del conversations[session_id]
        
        return GuidedLogState(
            session_id=session_id,
            question=None,
            is_complete=True,
            extracted_data=extracted_data
        )
        
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse completion JSON: {completion_message}")
        # If parsing fails, ask LLM to restructure
        conversations[session_id].append({
            "role": "user", 
            "content": "Please provide the final summary in the exact JSON format specified."
        })
        raise HTTPException(status_code=500, detail="Failed to parse completion data")


@app.get("/guided-log/status/{session_id}")
async def get_session_status(session_id: str):
    """
    Check if a session exists and get conversation history.
    Useful for debugging or reconnecting.
    """
    if session_id not in conversations:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "exists": True,
        "message_count": len(conversations[session_id])
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("GUIDED_LOG_PORT", "8001"))
    print(f"🚀 Guided Log Service starting on port {port}")
    print(f"   Lemonade URL: {LEMONADE_BASE}")
    print(f"   Model: {MODEL}")
    uvicorn.run("guided_log:app", host="0.0.0.0", port=port, reload=True, log_level="info")
