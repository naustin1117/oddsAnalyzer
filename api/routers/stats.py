"""
Statistics endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta
from typing import Optional

from ..auth import verify_api_key
from ..models import StatsResponse, PerformanceStats, ConfidenceStats
from ..services.data_loader import load_predictions

router = APIRouter(prefix="/stats", tags=["Statistics"])


@router.get("", response_model=StatsResponse)
async def get_stats(
    days: Optional[int] = Query(None, ge=1, le=365, description="Limit to last N days (optional)"),
    api_key: str = Depends(verify_api_key),
):
    """
    Get performance statistics.

    Args:
        days: Optional - limit to last N days
        api_key: API key from header (required)

    Returns:
        StatsResponse: Performance statistics overall and by confidence level
    """
    df = load_predictions()

    # Filter for verified results only
    verified = df[df['result'].notna() & (df['result'] != 'UNKNOWN')].copy()

    # Apply date filter if provided
    if days:
        cutoff_date = (datetime.now() - timedelta(days=days)).date()
        verified['game_date'] = verified['game_time'].dt.tz_convert('America/New_York').dt.date
        verified = verified[verified['game_date'] >= cutoff_date]

    if len(verified) == 0:
        raise HTTPException(status_code=404, detail="No verified results found")

    # Calculate overall stats
    total_bets = len(verified)
    wins = (verified['result'] == 'WIN').sum()
    losses = (verified['result'] == 'LOSS').sum()
    pushes = (verified['result'] == 'PUSH').sum()
    total_units = verified['units_won'].sum()
    win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
    roi = (total_units / total_bets * 100) if total_bets > 0 else 0

    overall = PerformanceStats(
        total_bets=total_bets,
        wins=int(wins),
        losses=int(losses),
        pushes=int(pushes),
        win_rate=round(win_rate, 1),
        total_units=round(total_units, 2),
        roi=round(roi, 1),
    )

    # Calculate stats by confidence level
    by_confidence = []
    for conf in ['HIGH', 'MEDIUM', 'LOW']:
        conf_bets = verified[verified['confidence'] == conf]
        if len(conf_bets) > 0:
            conf_total = len(conf_bets)
            conf_wins = (conf_bets['result'] == 'WIN').sum()
            conf_losses = (conf_bets['result'] == 'LOSS').sum()
            conf_pushes = (conf_bets['result'] == 'PUSH').sum()
            conf_units = conf_bets['units_won'].sum()
            conf_win_rate = (conf_wins / conf_total * 100)
            conf_roi = (conf_units / conf_total * 100)

            by_confidence.append(
                ConfidenceStats(
                    confidence=conf,
                    total_bets=conf_total,
                    wins=int(conf_wins),
                    losses=int(conf_losses),
                    pushes=int(conf_pushes),
                    win_rate=round(conf_win_rate, 1),
                    total_units=round(conf_units, 2),
                    roi=round(conf_roi, 1),
                )
            )

    return StatsResponse(
        overall=overall,
        by_confidence=by_confidence,
    )


@router.get("/confidence/{level}", response_model=ConfidenceStats)
async def get_confidence_stats(
    level: str,
    days: Optional[int] = Query(None, ge=1, le=365, description="Limit to last N days (optional)"),
    api_key: str = Depends(verify_api_key),
):
    """
    Get statistics for a specific confidence level.

    Args:
        level: Confidence level (HIGH, MEDIUM, or LOW)
        days: Optional - limit to last N days
        api_key: API key from header (required)

    Returns:
        ConfidenceStats: Statistics for the specified confidence level
    """
    level = level.upper()
    if level not in ['HIGH', 'MEDIUM', 'LOW']:
        raise HTTPException(status_code=400, detail="Invalid confidence level. Must be HIGH, MEDIUM, or LOW")

    df = load_predictions()

    # Filter for verified results only
    verified = df[df['result'].notna() & (df['result'] != 'UNKNOWN')].copy()

    # Apply date filter if provided
    if days:
        cutoff_date = (datetime.now() - timedelta(days=days)).date()
        verified['game_date'] = verified['game_time'].dt.tz_convert('America/New_York').dt.date
        verified = verified[verified['game_date'] >= cutoff_date]

    # Filter by confidence level
    conf_bets = verified[verified['confidence'] == level]

    if len(conf_bets) == 0:
        raise HTTPException(status_code=404, detail=f"No verified results found for {level} confidence")

    # Calculate stats
    conf_total = len(conf_bets)
    conf_wins = (conf_bets['result'] == 'WIN').sum()
    conf_losses = (conf_bets['result'] == 'LOSS').sum()
    conf_pushes = (conf_bets['result'] == 'PUSH').sum()
    conf_units = conf_bets['units_won'].sum()
    conf_win_rate = (conf_wins / conf_total * 100)
    conf_roi = (conf_units / conf_total * 100)

    return ConfidenceStats(
        confidence=level,
        total_bets=conf_total,
        wins=int(conf_wins),
        losses=int(conf_losses),
        pushes=int(conf_pushes),
        win_rate=round(conf_win_rate, 1),
        total_units=round(conf_units, 2),
        roi=round(conf_roi, 1),
    )