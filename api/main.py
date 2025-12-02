"""
NHL Shots Betting Analysis API

FastAPI backend to expose betting predictions and historical results.
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import pandas as pd
from typing import Optional, List

from .auth import verify_api_key
from .config import ALLOWED_ORIGINS, PREDICTIONS_FILE
from .models import (
    Prediction,
    PredictionsResponse,
    StatsResponse,
    PerformanceStats,
    ConfidenceStats,
    HealthResponse,
)

# Initialize FastAPI app
app = FastAPI(
    title="NHL Shots Betting API",
    description="API for NHL player shots betting predictions and results",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_predictions() -> pd.DataFrame:
    """Load predictions from CSV file."""
    try:
        df = pd.read_csv(PREDICTIONS_FILE)
        df['game_time'] = pd.to_datetime(df['game_time'])
        return df
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Predictions file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading predictions: {str(e)}")


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API information."""
    return {
        "name": "NHL Shots Betting API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint - no authentication required."""
    df = load_predictions()
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        predictions_count=len(df),
    )


@app.get("/predictions/today", response_model=PredictionsResponse, tags=["Predictions"])
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


@app.get("/predictions/upcoming", response_model=PredictionsResponse, tags=["Predictions"])
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


@app.get("/results", response_model=PredictionsResponse, tags=["Results"])
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


@app.get("/stats", response_model=StatsResponse, tags=["Statistics"])
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


@app.get("/stats/confidence/{level}", response_model=ConfidenceStats, tags=["Statistics"])
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)