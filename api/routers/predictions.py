"""
Predictions endpoints.
"""
import logging
import pytz
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd

from ..auth import verify_api_key
from ..models import Prediction, PredictionsResponse
from ..services.data_loader import load_predictions

router = APIRouter(prefix="/predictions", tags=["Predictions"])
logger = logging.getLogger(__name__)


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
    logger.info("="*60)
    logger.info("📅 GET TODAY'S PREDICTIONS")
    logger.info(f"  Confidence filter: {confidence}")

    df = load_predictions()
    logger.info(f"  Total predictions loaded: {len(df)}")

    # Filter for today's games (in EST timezone)
    est = pytz.timezone('America/New_York')
    today = datetime.now(est)
    logger.info(f"  Today's date (EST): {today.date()}")
    logger.info(f"  Server UTC time: {datetime.utcnow()}")

    # Convert timezone-aware datetimes to EST
    df['game_date'] = df['game_time'].dt.tz_convert('America/New_York').dt.date

    # Show sample dates
    unique_dates = df['game_date'].unique()
    logger.info(f"  Unique dates in predictions: {sorted(unique_dates)[:10]}")

    today_predictions = df[df['game_date'] == today.date()].copy()
    logger.info(f"  Predictions for today: {len(today_predictions)}")

    if len(today_predictions) > 0:
        logger.info(f"  Sample player_ids: {today_predictions['player_id'].head(5).tolist()}")
        logger.info(f"  Confidence breakdown: {today_predictions['confidence'].value_counts().to_dict()}")

    # Apply confidence filter if provided
    if confidence:

        confidence = confidence.upper()
        if confidence not in ['HIGH', 'MEDIUM', 'LOW']:
            raise HTTPException(status_code=400, detail="Invalid confidence level. Must be HIGH, MEDIUM, or LOW")
        today_predictions = today_predictions[today_predictions['confidence'] == confidence]
        logger.info(f"  After confidence filter: {len(today_predictions)} predictions")

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

    logger.info(f"✅ Returning {len(predictions)} predictions to client")
    if len(predictions) > 0:
        logger.info(f"  Player IDs being returned: {[p.player_id for p in predictions[:5]]}")
    logger.info("="*60)

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

    # Filter for future games (in EST timezone)
    est = pytz.timezone('America/New_York')
    now = datetime.now(est)
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