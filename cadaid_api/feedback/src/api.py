from fastapi import FastAPI, HTTPException, Form, Depends, status, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import asyncio
import os
import json
import datetime
from sqlalchemy.orm import Session
from shared.utils.logger import cadaid_logger
from shared.utils.data_structures import Metadata
from shared.auth import get_api_key
from shared.db.db import get_session
# Set up logger
logger = cadaid_logger(__name__)

# Load environment variables
logger.info("Loading environment variables")
load_dotenv("/app/shared/.env.dev")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Feedback API")
    await asyncio.sleep(5)
    logger.info("Feedback API ready")
    yield
    # Shutdown
    logger.info("Shutting down Feedback API")

# Set up FastAPI app
app = FastAPI(root_path="/feedback",
              root_path_in_servers=True,
              title="Feedback API",
              description="API for feedback submission using CADAID system",
              version="1.0.0",
              docs_url="/docs",
              open_api_url="/openapi.json",
              openapi_tags=[{
                "name": "Feedback",
                "description": "API for feedback submission to further improve the CADAID system"
              }], 
              swagger_ui_init_oauth={
                  "apiKeyName": "X-API-Key"
              }
        )

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class Feedback(BaseModel):
    filename: str
    is_correct: bool




@app.post("/feedback")
async def feedback(feedback: Feedback, session: Session = Depends(get_session)):
    existing_metadata = session.query(Metadata).filter(Metadata.filename == feedback.filename).first()

    if not existing_metadata:
        raise HTTPException(status_code=404, detail="Metadata not found")
    existing_metadata.is_correct = feedback.is_correct 
    session.commit()  

    return {"message": "Feedback submitted", "filename": feedback.filename, "is_correct": feedback.is_correct}
    

# Endpoint to check log file
@app.get("/logs/")
async def get_logs():
    try:
        with open('/app/logs/app.log', 'r') as log_file:
            logs = log_file.read()
        return {"logs": logs}
    except Exception as e:
        logger.error(f"Error fetchcing logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not fetch logs")