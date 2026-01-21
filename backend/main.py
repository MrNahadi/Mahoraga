"""
Mahoraga - Autonomous Bug Triage Engine
Main FastAPI application entry point
"""

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from database import init_database, check_database_health, get_db
from sqlalchemy.orm import Session
from webhook_handler import webhook_handler
from api_endpoints import router as api_router
from error_handling import get_system_health, comprehensive_logger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Mahoraga Triage Engine",
    description="Autonomous bug triage system that analyzes, assigns, and drafts fixes",
    version="1.0.0"
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        init_database()
        logger.info("Database initialized successfully")
        
        # Start webhook job processing in background
        asyncio.create_task(webhook_handler.start_job_processing())
        logger.info("Webhook job processing started")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        webhook_handler.stop_job_processing()
        logger.info("Webhook job processing stopped")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Mahoraga Triage Engine is running"}

@app.get("/health")
async def health_check():
    """System health check including database status and external services"""
    db_health = check_database_health()
    system_health = get_system_health()
    
    # Determine overall status
    overall_status = "healthy"
    if db_health["status"] != "healthy":
        overall_status = "degraded"
    if system_health["overall_status"] in ["critical", "offline"]:
        overall_status = "critical"
    elif system_health["overall_status"] == "degraded" and overall_status == "healthy":
        overall_status = "degraded"
    
    return {
        "status": overall_status,
        "service": "mahoraga-triage-engine",
        "version": "1.0.0",
        "timestamp": system_health["timestamp"],
        "database": db_health,
        "external_services": system_health["services"],
        "degraded_services": system_health["degraded_services"]
    }

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with circuit breaker status and metrics"""
    db_health = check_database_health()
    system_health = get_system_health()
    
    return {
        "database": db_health,
        "system_health": system_health,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/database/health")
async def database_health():
    """Detailed database health check"""
    return check_database_health()

@app.post("/webhook/github")
async def github_webhook(request: Request):
    """
    GitHub webhook endpoint for receiving issue and PR events
    
    Handles:
    - Webhook signature verification using HMAC-SHA256
    - Issue and PR event parsing
    - Duplicate detection within configurable time window
    - Async job queuing for triage processing
    """
    return await webhook_handler.handle_webhook(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)