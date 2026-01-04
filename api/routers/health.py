"""
Health check endpoints.
"""
from fastapi import APIRouter
from datetime import datetime

from ..models import HealthResponse
from ..services.data_loader import load_predictions

router = APIRouter(tags=["Health"])


@router.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "name": "NHL Shots Betting API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint - no authentication required."""
    try:
        df = load_predictions()
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            predictions_count=len(df),
        )
    except Exception as e:
        # Return degraded status if predictions can't be loaded
        # but the API itself is running
        return HealthResponse(
            status="degraded",
            timestamp=datetime.now().isoformat(),
            predictions_count=0,
        )