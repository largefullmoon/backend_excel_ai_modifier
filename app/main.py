"""
FastAPI backend for Excel Viewer & AI Modifier
Main application entry point using modular architecture
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .routes import health_router, excel_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Handles Excel file processing and AI-based data enrichment"
)

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Include routers
app.include_router(health_router, tags=["Health"])
app.include_router(excel_router, tags=["Excel Processing"])

# Log startup information
@app.on_event("startup")
async def startup_event():
    """Log startup information"""
    logger.info(f"Starting {settings.API_TITLE} v{settings.API_VERSION}")
    logger.info(f"OpenAI configured: {'Yes' if settings.OPENAI_API_KEY else 'No'}")
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown information"""
    logger.info("Application shutdown complete")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
