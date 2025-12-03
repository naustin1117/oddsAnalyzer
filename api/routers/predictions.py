"""
Predictions endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta
from typing import Optional

from ..auth import verify_api_key
from ..models import Prediction, PredictionsResponse
from ..services.data_loader import load_predictions

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.get("/today", response_model=PredictionsResponse)
async def get_todays_predictions(
    confidence: Optional[str] = Query(None, description="Filter by confidence level: HIGH, MEDIUM, LOW"),
    api_key: str = Depends(verify_api_key),
):
    """
    Get today's betting predictions.

    Args:
        confidence: Optional filter by confidence level
        api_key: API key from header (required)

    Returns:
        PredictionsResponse: Today's predictions
    """
    df = load_predictions()

    # Filter for today's games (in EST timezone)
    today = datetime.now()
    df['game_date'] = df['game_time'].dt.tz_convert('America/New_York').dt.date

    today_predictions = df[df['game_date'] == today.date()].copy()

    # Apply confidence filter if provided
    if confidence:
        confidence = confidence.upper()
        if confidence not in ['HIGH', 'MEDIUM', 'LOW']:
            raise HTTPException(status_code=400, detail="Invalid confidence level. Must be HIGH, MEDIUM, or LOW")
        today_predictions = today_predictions[today_predictions['confidence'] == confidence]

    # Sort by game time
    today_predictions = today_predictions.sort_values('game_time')

    # Convert to list of Prediction models
    predictions = [
        Prediction(**row.to_dict())
        for _, row in today_predictions.iterrows()
    ]

    return PredictionsResponse(
        count=len(predictions),
        predictions=predictions,
    )


@router.get("/upcoming", response_model=PredictionsResponse)
async def get_upcoming_predictions(
    days: int = Query(7, ge=1, le=30, description="Number of days ahead to fetch"),
    confidence: Optional[str] = Query(None, description="Filter by confidence level: HIGH, MEDIUM, LOW"),
    api_key: str = Depends(verify_api_key),
):
    """
    Get upcoming predictions for the next N days.

    Args:
        days: Number of days ahead (1-30)
        confidence: Optional filter by confidence level
        api_key: API key from header (required)

    Returns:
        PredictionsResponse: Upcoming predictions
    """
    df = load_predictions()

    # Filter for future games
    now = datetime.now()
    end_date = (now + timedelta(days=days)).date()

    df['game_date'] = df['game_time'].dt.tz_convert('America/New_York').dt.date
    upcoming = df[
        (df['game_date'] >= now.date()) &
        (df['game_date'] <= end_date)
    ].copy()

    # Apply confidence filter if provided
    if confidence:
        confidence = confidence.upper()
        if confidence not in ['HIGH', 'MEDIUM', 'LOW']:
            raise HTTPException(status_code=400, detail="Invalid confidence level. Must be HIGH, MEDIUM, or LOW")
        upcoming = upcoming[upcoming['confidence'] == confidence]

    # Sort by game time
    upcoming = upcoming.sort_values('game_time')

    # Convert to list of Prediction models
    predictions = [
        Prediction(**row.to_dict())
        for _, row in upcoming.iterrows()
    ]

    return PredictionsResponse(
        count=len(predictions),
        predictions=predictions,
    )