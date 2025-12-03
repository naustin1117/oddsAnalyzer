"""
Pydantic models for API responses
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class Prediction(BaseModel):
    """Single prediction/bet recommendation"""
    game_id: str
    nhl_game_id: Optional[int]
    game_time: str
    away_team: str
    home_team: str
    player_id: int
    player_name: str
    player_team: str
    line: float
    over_odds: int
    under_odds: int
    recommendation: str
    confidence: str
    edge: float
    model_prob: float
    implied_prob: float
    actual_shots: Optional[int] = None
    result: Optional[str] = None
    units_won: Optional[float] = None
    prediction_date: str


class PredictionsResponse(BaseModel):
    """Response containing multiple predictions"""
    count: int
    predictions: List[Prediction]


class PerformanceStats(BaseModel):
    """Performance statistics"""
    total_bets: int
    wins: int
    losses: int
    pushes: int
    win_rate: float
    total_units: float
    roi: float


class ConfidenceStats(BaseModel):
    """Statistics for a specific confidence level"""
    confidence: str
    total_bets: int
    wins: int
    losses: int
    pushes: int
    win_rate: float
    total_units: float
    roi: float


class StatsResponse(BaseModel):
    """Overall statistics response"""
    overall: PerformanceStats
    by_confidence: List[ConfidenceStats]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    predictions_count: int


class PlayerGame(BaseModel):
    """Single game stats for a player"""
    game_date: str
    opponent: str
    home_away: str
    shots: int
    goals: int
    assists: int
    points: int
    toi_seconds: float
    game_id: Optional[int] = None


class PlayerGamesResponse(BaseModel):
    """Response containing player's recent games"""
    player_id: int
    player_name: str
    team: str
    games_count: int
    games: List[PlayerGame]
    averages: dict


class PlayerPredictionsResponse(BaseModel):
    """Response containing predictions for a specific player"""
    player_id: int
    player_name: str
    upcoming_count: int
    historical_count: int
    upcoming: List[Prediction]
    historical: List[Prediction]