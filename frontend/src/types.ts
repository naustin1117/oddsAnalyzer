/**
 * TypeScript types matching the FastAPI backend Pydantic models
 */

export interface Prediction {
  game_id: string;
  nhl_game_id: number | null;
  game_time: string;
  away_team: string;
  home_team: string;
  player_id: number;
  player_name: string;
  player_team: string;
  line: number;
  over_odds: number;
  under_odds: number;
  prediction: number | null;
  recommendation: string;
  confidence: string;
  edge: number | null;
  model_prob: number | null;
  implied_prob: number | null;
  actual_shots: number | null;
  result: string | null;
  units_won: number | null;
  prediction_date: string;
}

export interface PredictionsResponse {
  count: number;
  predictions: Prediction[];
}

export interface BetTypeStats {
  total_bets: number;
  wins: number;
  losses: number;
  pushes: number;
  win_rate: number;
  total_units: number;
  roi: number;
}

export interface ResultsSummaryResponse {
  confidence: string;
  over_bets: BetTypeStats;
  under_bets: BetTypeStats;
  total: BetTypeStats;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  predictions_count: number;
}

export interface PlayerGame {
  game_date: string;
  opponent: string;
  home_away: string;
  shots: number;
  goals: number;
  assists: number;
  points: number;
  toi_seconds: number;
  game_id: number | null;
}

export interface PlayerAverages {
  shots_per_game: number;
  goals_per_game: number;
  assists_per_game: number;
  points_per_game: number;
  toi_per_game: number;
}

export interface PlayerGamesResponse {
  player_id: number;
  player_name: string;
  team: string;
  headshot_url: string;
  games_count: number;
  games: PlayerGame[];
  averages: PlayerAverages;
}

export interface PlayerPredictionsResponse {
  player_id: number;
  player_name: string;
  upcoming_count: number;
  historical_count: number;
  upcoming: Prediction[];
  historical: Prediction[];
}