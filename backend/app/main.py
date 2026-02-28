from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="VoiceHealth Tracker API")

# Enable CORS for frontend
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
def quick_log(data: dict):
    """Placeholder for quick log endpoint"""
    return {
        "status": "success",
        "message": "Quick log placeholder - Noah will implement",
        "symptoms": ["headache"],
        "severity": 7,
        "potential_triggers": ["stress"],
        "data_received": data
    }

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
