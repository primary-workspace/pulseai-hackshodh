"""
Pulse AI - Main Application
Clinical surveillance platform for early health warning
"""

import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db, init_db
from app.routes import health, analysis, escalation, users, webhook, auth, dashboard, oauth
from app.services.synthetic_data import SyntheticDataGenerator
from app.services.gemini_service import GeminiService

# Initialize FastAPI app
app = FastAPI(
    title="Pulse AI",
    description="Continuous clinical surveillance platform for early health warning",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "*"  # For development - restrict in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for requests
class Prompt(BaseModel):
    text: str


# Include routers
app.include_router(users.router)
app.include_router(health.router)
app.include_router(analysis.router)
app.include_router(escalation.router)
app.include_router(webhook.router)    # Health Connect webhook
app.include_router(auth.router)       # Authentication & API keys
app.include_router(dashboard.router)  # Dashboard data endpoints
app.include_router(oauth.router)      # Google OAuth & Drive ingestion


@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    init_db()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Pulse AI",
        "version": "1.0.0",
        "description": "Clinical surveillance platform for early health warning",
        "status": "online"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/generate")
async def generate(prompt: Prompt):
    """
    Proxy to Gemini API for AI-generated insights
    """
    gemini = GeminiService()
    result = await gemini.generate(prompt.text)
    return result


@app.get("/gemini/health")
async def gemini_health():
    """Check Gemini API health"""
    gemini = GeminiService()
    return await gemini.health_check()


@app.post("/demo/generate")
def generate_demo_data(db: Session = Depends(get_db)):
    """
    Generate demo data for testing
    """
    generator = SyntheticDataGenerator(db)
    result = generator.generate_complete_demo()
    return {
        "success": True,
        "message": "Demo data generated successfully",
        "data": result
    }


@app.post("/demo/compute-scores")
def compute_demo_scores(db: Session = Depends(get_db)):
    """
    Compute CareScores for demo user
    """
    from app.models.user import User
    from app.models.health_data import HealthData
    from app.services.carescore_engine import CareScoreEngine
    from app.services.anomaly_detector import AnomalyDetector
    from datetime import datetime, timedelta
    
    # Get demo user
    user = db.query(User).filter(User.email == "demo@pulseai.com").first()
    if not user:
        return {"error": "Demo user not found. Run /demo/generate first."}
    
    # Train baseline
    detector = AnomalyDetector(db)
    detector.learn_baseline(user.id, days=14)
    
    # Compute CareScore from latest data
    engine = CareScoreEngine(db)
    
    latest = db.query(HealthData).filter(
        HealthData.user_id == user.id
    ).order_by(HealthData.timestamp.desc()).first()
    
    if not latest:
        return {"error": "No health data found"}
    
    current_data = {
        "heart_rate": latest.heart_rate,
        "hrv": latest.hrv,
        "sleep_duration": latest.sleep_duration,
        "activity_level": latest.activity_level,
        "breathing_rate": latest.breathing_rate,
        "bp_systolic": latest.bp_systolic,
        "bp_diastolic": latest.bp_diastolic,
        "blood_sugar": latest.blood_sugar
    }
    
    care_score = engine.compute_carescore(user.id, current_data)
    
    return {
        "success": True,
        "user_id": user.id,
        "care_score": care_score.care_score,
        "status": care_score.status,
        "explanation": care_score.explanation
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
