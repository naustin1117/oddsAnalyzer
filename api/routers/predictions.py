"""
Predictions endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd

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
    # Convert timezone-aware datetimes to EST
    df['game_date'] = df['game_time'].dt.tz_convert('America/New_York').dt.date

    today_predictions = df[df['game_date'] == today.date()].copy()

    # Apply confidence filter if provided
    if confidence:
        confidence = confidence.upper()
        if confidence not in ['HIGH', 'MEDIUM', 'LOW']:
            raise HTTPException(status_code=400, detail="Invalid confidence level. Must be HIGH, MEDIUM, or LOW")
        today_predictions = today_predictions[today_predictions['confidence'] == confidence]

    # Sort by confidence (HIGH to LOW) then by game time
    today_predictions['confidence_order'] = pd.Categorical(
        today_predictions['confidence'],
        categories=['HIGH', 'MEDIUM', 'LOW'],
        ordered=True
    )
    today_predictions = today_predictions.sort_values(['confidence_order', 'game_time'])
    today_predictions = today_predictions.drop('confidence_order', axis=1)

    # Convert to list of Prediction models
    predictions = []
    for _, row in today_predictions.iterrows():
        row_dict = row.to_dict()

        # Convert Timestamp to string
        if pd.notna(row_dict.get('game_time')):
            row_dict['game_time'] = row['game_time'].isoformat()

        # Map CSV column names to model field names
        row_dict['player_team'] = row_dict.pop('team', None)
        row_dict['model_prob'] = row_dict.pop('model_probability', None)
        row_dict['implied_prob'] = row_dict.pop('implied_probability', None)

        # Convert all NaN values to None (required for JSON serialization)
        row_dict = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}

        predictions.append(Prediction(**row_dict))

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

    # Convert timezone-aware datetimes to EST
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

    # Sort by confidence (HIGH to LOW) then by game time
    upcoming['confidence_order'] = pd.Categorical(
        upcoming['confidence'],
        categories=['HIGH', 'MEDIUM', 'LOW'],
        ordered=True
    )
    upcoming = upcoming.sort_values(['confidence_order', 'game_time'])
    upcoming = upcoming.drop('confidence_order', axis=1)

    # Convert to list of Prediction models
    predictions = []
    for _, row in upcoming.iterrows():
        row_dict = row.to_dict()

        # Convert Timestamp to string
        if pd.notna(row_dict.get('game_time')):
            row_dict['game_time'] = row['game_time'].isoformat()

        # Map CSV column names to model field names
        row_dict['player_team'] = row_dict.pop('team', None)
        row_dict['model_prob'] = row_dict.pop('model_probability', None)
        row_dict['implied_prob'] = row_dict.pop('implied_probability', None)

        # Convert all NaN values to None (required for JSON serialization)
        row_dict = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}

        predictions.append(Prediction(**row_dict))

    return PredictionsResponse(
        count=len(predictions),
        predictions=predictions,
    )