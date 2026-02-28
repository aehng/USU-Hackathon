from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os

from database import get_db, engine
from models import models

# Import our Analysis Engine
from services.analysis import compute_all_stats

# Create database tables if they don't exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="VoiceHealth Tracker API")

# Setup CORS so the frontend dashboard can access this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:5173")], # Vite's default dev port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    """Health check endpoint to ensure the API is running."""
    return {"status": "ok"}

@app.get("/api/stats/{user_id}")
def get_user_stats(user_id: str, db: Session = Depends(get_db)):
    """
    Computes and returns the trigger correlations, temporal patterns, 
    and severity trends for the user's dashboard visualizations.
    """
    try:
        stats = compute_all_stats(user_id, db)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/entries/{user_id}")
def get_user_entries(
    user_id: str, 
    limit: int = Query(20, ge=1, le=100), 
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Returns a paginated list of the user's logged entries, sorted most recent first.
    Used for the history/log view in the frontend.
    """
    try:
        entries = db.query(models.Entry)\
            .filter(models.Entry.user_id == user_id)\
            .order_by(models.Entry.logged_at.desc())\
            .offset(offset)\
            .limit(limit)\
            .all()
            
        return [entry.__dict__ for entry in entries]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Note: Other endpoints like /api/log/quick and /api/insights are owned by Noah
# and will be added by him when he works on the LLM backend integration.
