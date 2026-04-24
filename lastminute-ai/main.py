"""
LastMinute AI — FastAPI Backend
Run: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn

from routers import ingest, qa, practice, mindmap
from database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="LastMinute AI API",
    description="AI-powered last-minute doubt resolver for students",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router,   prefix="/api/ingest",   tags=["Document Ingestion"])
app.include_router(qa.router,       prefix="/api/qa",       tags=["Q&A"])
app.include_router(practice.router, prefix="/api/practice", tags=["Past Paper Practice"])
app.include_router(mindmap.router,  prefix="/api/mindmap",  tags=["Mind Map"])

@app.get("/")
async def root():
    return {"message": "LastMinute AI API is running", "docs": "/docs"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
