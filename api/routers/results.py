"""
Results endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta
from typing import Optional

from ..auth import verify_api_key
from ..models import Prediction, PredictionsResponse
from ..services.data_loader import load_predictions

router = APIRouter(prefix="/results", tags=["Results"])


@router.get("", response_model=PredictionsResponse)
async def get_results(
    days: int = Query(30, ge=1, le=365, description="Number of days back to fetch"),
    confidence: Optional[str] = Query(None, description="Filter by confidence level: HIGH, MEDIUM, LOW"),
    result: Optional[str] = Query(None, description="Filter by result: WIN, LOSS, PUSH"),
    api_key: str = Depends(verify_api_key),
):
    """
    Get historical betting results.

    Args:
        days: Number of days back (1-365)
        confidence: Optional filter by confidence level
        result: Optional filter by result type
        api_key: API key from header (required)

    Returns:
        PredictionsResponse: Historical results
    """
    df = load_predictions()

    # Filter for verified results only
    results_df = df[df['result'].notna() & (df['result'] != 'UNKNOWN')].copy()

    # Filter by date range
    cutoff_date = (datetime.now() - timedelta(days=days)).date()
    results_df['game_date'] = results_df['game_time'].dt.tz_convert('America/New_York').dt.date
    results_df = results_df[results_df['game_date'] >= cutoff_date]

    # Apply confidence filter if provided
    if confidence:
        confidence = confidence.upper()
        if confidence not in ['HIGH', 'MEDIUM', 'LOW']:
            raise HTTPException(status_code=400, detail="Invalid confidence level. Must be HIGH, MEDIUM, or LOW")
        results_df = results_df[results_df['confidence'] == confidence]

    # Apply result filter if provided
    if result:
        result = result.upper()
        if result not in ['WIN', 'LOSS', 'PUSH']:
            raise HTTPException(status_code=400, detail="Invalid result. Must be WIN, LOSS, or PUSH")
        results_df = results_df[results_df['result'] == result]

    # Sort by game time (most recent first)
    results_df = results_df.sort_values('game_time', ascending=False)

    # Convert to list of Prediction models
    predictions = [
        Prediction(**row.to_dict())
        for _, row in results_df.iterrows()
    ]

    return PredictionsResponse(
        count=len(predictions),
        predictions=predictions,
    )