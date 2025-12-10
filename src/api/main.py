"""
FastAPI Application Entry Point
AI Research Agent System REST API
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import research, content, pipelines, social, branding, paper
from src.api.middleware import (
    ErrorHandlerMiddleware,
    RequestLoggingMiddleware,
    RequestValidationMiddleware,
)
from src.common.database import init_db
from src.common.config import config
from src.common.logger import setup_logger

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager"""
    # Startup
    logger.info("Starting AI Research Agent API...")
    await init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down AI Research Agent API...")


app = FastAPI(
    title="AI Research Agent API",
    description="Deep research and content generation for AI topics",
    version="1.0.0",
    lifespan=lifespan,
)

# Add custom middleware (order matters - last added runs first)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestValidationMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(research.router, prefix="/api/v1/research", tags=["Research"])
app.include_router(paper.router, prefix="/api/v1/paper", tags=["Paper Research"])
app.include_router(content.router, prefix="/api/v1/content", tags=["Content"])
app.include_router(pipelines.router, prefix="/api/v1/pipelines", tags=["Pipelines"])
app.include_router(social.router, prefix="/api/v1/social", tags=["Social Content"])
app.include_router(branding.router, prefix="/api/v1/branding", tags=["Branding"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AI Research Agent API",
        "version": "1.0.0",
        "status": "healthy",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

