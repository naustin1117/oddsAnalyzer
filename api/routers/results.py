"""
Results endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd

from ..auth import verify_api_key
from ..models import Prediction, PredictionsResponse, ResultsSummaryResponse, BetTypeStats
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
    predictions = []
    for _, row in results_df.iterrows():
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


@router.get("/summary", response_model=ResultsSummaryResponse)
async def get_results_summary(
    confidence: str = Query("HIGH", description="Confidence level: HIGH, MEDIUM, LOW"),
    days: int = Query(365, ge=1, le=365, description="Number of days back to analyze"),
    api_key: str = Depends(verify_api_key),
):
    """
    Get summary of results by bet type (OVER/UNDER) for a specific confidence level.

    Args:
        confidence: Confidence level (default: HIGH)
        days: Number of days back (default: 365)
        api_key: API key from header (required)

    Returns:
        ResultsSummaryResponse: Summary statistics split by OVER/UNDER bets
    """
    df = load_predictions()

    # Validate confidence level
    confidence = confidence.upper()
    if confidence not in ['HIGH', 'MEDIUM', 'LOW']:
        raise HTTPException(status_code=400, detail="Invalid confidence level. Must be HIGH, MEDIUM, or LOW")

    # Filter for verified results only
    results_df = df[df['result'].notna() & (df['result'] != 'UNKNOWN')].copy()

    # Filter by date range
    cutoff_date = (datetime.now() - timedelta(days=days)).date()
    results_df['game_date'] = results_df['game_time'].dt.tz_convert('America/New_York').dt.date
    results_df = results_df[results_df['game_date'] >= cutoff_date]

    # Filter by confidence level
    results_df = results_df[results_df['confidence'] == confidence]

    # Determine bet type (OVER or UNDER) from recommendation
    results_df['bet_type'] = results_df['recommendation'].apply(
        lambda x: 'OVER' if 'OVER' in str(x).upper() else 'UNDER' if 'UNDER' in str(x).upper() else 'UNKNOWN'
    )

    # Calculate stats for OVER bets
    over_bets = results_df[results_df['bet_type'] == 'OVER']
    over_wins = len(over_bets[over_bets['result'] == 'WIN'])
    over_losses = len(over_bets[over_bets['result'] == 'LOSS'])
    over_pushes = len(over_bets[over_bets['result'] == 'PUSH'])
    over_total = len(over_bets)
    over_win_rate = (over_wins / over_total * 100) if over_total > 0 else 0
    over_units = over_bets['units_won'].sum() if len(over_bets) > 0 else 0
    over_roi = (over_units / over_total * 100) if over_total > 0 else 0

    # Calculate stats for UNDER bets
    under_bets = results_df[results_df['bet_type'] == 'UNDER']
    under_wins = len(under_bets[under_bets['result'] == 'WIN'])
    under_losses = len(under_bets[under_bets['result'] == 'LOSS'])
    under_pushes = len(under_bets[under_bets['result'] == 'PUSH'])
    under_total = len(under_bets)
    under_win_rate = (under_wins / under_total * 100) if under_total > 0 else 0
    under_units = under_bets['units_won'].sum() if len(under_bets) > 0 else 0
    under_roi = (under_units / under_total * 100) if under_total > 0 else 0

    # Calculate total stats
    total_wins = over_wins + under_wins
    total_losses = over_losses + under_losses
    total_pushes = over_pushes + under_pushes
    total_bets = over_total + under_total
    total_win_rate = (total_wins / total_bets * 100) if total_bets > 0 else 0
    total_units = over_units + under_units
    total_roi = (total_units / total_bets * 100) if total_bets > 0 else 0

    return ResultsSummaryResponse(
        confidence=confidence,
        over_bets=BetTypeStats(
            total_bets=over_total,
            wins=over_wins,
            losses=over_losses,
            pushes=over_pushes,
            win_rate=round(over_win_rate, 1),
            total_units=round(over_units, 2),
            roi=round(over_roi, 1)
        ),
        under_bets=BetTypeStats(
            total_bets=under_total,
            wins=under_wins,
            losses=under_losses,
            pushes=under_pushes,
            win_rate=round(under_win_rate, 1),
            total_units=round(under_units, 2),
            roi=round(under_roi, 1)
        ),
        total=BetTypeStats(
            total_bets=total_bets,
            wins=total_wins,
            losses=total_losses,
            pushes=total_pushes,
            win_rate=round(total_win_rate, 1),
            total_units=round(total_units, 2),
            roi=round(total_roi, 1)
        )
    )