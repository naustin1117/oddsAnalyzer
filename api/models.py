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
    away_team_abbrev: Optional[str] = None
    home_team_abbrev: Optional[str] = None
    player_id: int
    player_name: str
    player_team: str
    player_team_name: Optional[str] = None
    line: float
    over_odds: int
    under_odds: int
    prediction: Optional[float] = None
    recommendation: str
    confidence: str
    edge: Optional[float] = None
    model_prob: Optional[float] = None
    implied_prob: Optional[float] = None
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


class BetTypeStats(BaseModel):
    """Statistics for a specific bet type (OVER/UNDER)"""
    total_bets: int
    wins: int
    losses: int
    pushes: int
    win_rate: float
    total_units: float
    roi: float


class ResultsSummaryResponse(BaseModel):
    """Summary of results by bet type"""
    confidence: str
    over_bets: BetTypeStats
    under_bets: BetTypeStats
    total: BetTypeStats


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    predictions_count: int


class PlayerGame(BaseModel):
    """Single game stats for a player"""
    game_date: str
    opponent: str
    opponent_logo_url: str
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
    team_abbrev: str
    team_name: str
    headshot_url: str
    team_logo_url: str
    primary_color: str
    secondary_color: str
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


class LineupPlayer(BaseModel):
    """Single player in a lineup"""
    player_id: Optional[int] = None
    player_name: str
    position: str
    position_id: str
    line: str
    line_id: str
    jersey_number: Optional[float] = None
    headshot_url: Optional[str] = None
    injury_status: Optional[str] = None
    game_time_decision: Optional[bool] = None


class TeamLineup(BaseModel):
    """Lineup for a single team"""
    team: str
    team_name: str
    team_logo_url: str
    primary_color: str
    secondary_color: str
    opponent: Optional[str] = None
    opponent_name: Optional[str] = None
    line_combinations: List[LineupPlayer]
    goalies: List[LineupPlayer]
    injuries: List[LineupPlayer]


class LineupsResponse(BaseModel):
    """Response containing lineups for a team and their opponent"""
    team: TeamLineup
    opponent: Optional[TeamLineup] = None


class PlayerNewsItem(BaseModel):
    """Single news item for a player"""
    team: str
    player_id: Optional[int] = None
    player_name: str
    created_at: str
    details: str
    fantasy_details: str
    scrape_date: str


class PlayerNewsResponse(BaseModel):
    """Response containing news for a player"""
    player_id: Optional[int] = None
    player_name: str
    news_count: int
    news: List[PlayerNewsItem]


class BulkPlayerGamesRequest(BaseModel):
    """Request for bulk player games data"""
    player_ids: List[int]
    limit: int = 10


class BulkPlayerGamesResponse(BaseModel):
    """Response containing recent games for multiple players"""
    count: int
    players: List[PlayerGamesResponse]