"""
Health check endpoints.
"""
import logging
from fastapi import APIRouter, Request
from datetime import datetime

from ..models import HealthResponse
from ..services.data_loader import load_predictions

router = APIRouter(tags=["Health"])
logger = logging.getLogger(__name__)


@router.get("/")
async def root():
    """Root endpoint - API information."""
    logger.info("📍 Root endpoint called")
    return {
        "name": "NHL Shots Betting API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    """Health check endpoint - no authentication required."""
    logger.info("="*60)
    logger.info("💓 HEALTH CHECK REQUEST")
    logger.info(f"  Method: {request.method}")
    logger.info(f"  Headers: {dict(request.headers)}")
    logger.info(f"  Client: {request.client}")

    try:
        logger.info("  Loading predictions...")
        df = load_predictions()
        logger.info(f"✅ Health check passed: {len(df)} predictions loaded")
        logger.info("="*60)
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            predictions_count=len(df),
        )
    except Exception as e:
        # Return degraded status if predictions can't be loaded
        # but the API itself is running
        logger.error(f"⚠️  Health check degraded: {str(e)}")
        logger.info("="*60)
        return HealthResponse(
            status="degraded",
            timestamp=datetime.now().isoformat(),
            predictions_count=0,
        )