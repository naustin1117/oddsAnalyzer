"""
Player-specific endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime
import pandas as pd

from ..auth import verify_api_key
from ..models import PlayerGame, PlayerGamesResponse, Prediction, PlayerPredictionsResponse
from ..services.data_loader import load_predictions, load_player_logs, load_player_name_mapping, load_team_logos

router = APIRouter(prefix="/players", tags=["Players"])


@router.get("/{player_id}/recent-games", response_model=PlayerGamesResponse)
async def get_player_recent_games(
    player_id: int,
    limit: int = Query(10, ge=1, le=50, description="Number of recent games to fetch"),
    api_key: str = Depends(verify_api_key),
):
    """
    Get a player's recent game-by-game statistics.

    Args:
        player_id: NHL player ID
        limit: Number of recent games (1-50, default 10)
        api_key: API key from header (required)

    Returns:
        PlayerGamesResponse: Player's recent games with stats and averages
    """
    df = load_player_logs()

    # Filter for this player
    player_games = df[df['player_id'] == player_id].copy()

    if len(player_games) == 0:
        raise HTTPException(status_code=404, detail=f"No games found for player ID {player_id}")

    # Sort by date (most recent first) and limit
    player_games['game_date'] = pd.to_datetime(player_games['game_date'])
    player_games = player_games.sort_values('game_date', ascending=False).head(limit)

    # Get player info from name mapping
    player_mapping = load_player_name_mapping()
    player_info = player_mapping[player_mapping['player_id'] == player_id]

    if len(player_info) == 0:
        raise HTTPException(status_code=404, detail=f"Player name not found for player ID {player_id}")

    player_name = player_info.iloc[0]['player_name']
    headshot_url = player_info.iloc[0]['headshot_url']
    player_team = player_games.iloc[0]['team_abbrev']

    # Get team logo URL and colors
    team_logos = load_team_logos()
    team_logo_row = team_logos[team_logos['team_abbrev'] == player_team]
    if len(team_logo_row) > 0:
        team_logo_url = team_logo_row.iloc[0]['logo_url']
        primary_color = team_logo_row.iloc[0]['primary_color']
        secondary_color = team_logo_row.iloc[0]['secondary_color']
    else:
        team_logo_url = ""
        primary_color = "#000000"
        secondary_color = "#FFFFFF"

    # Convert to PlayerGame models
    games = []
    for _, game in player_games.iterrows():
        # Convert home_flag (0 or 1) to home_away ("HOME" or "AWAY")
        home_away = "HOME" if game['home_flag'] == 1 else "AWAY"

        # Convert toi_minutes to seconds for the model
        toi_seconds = float(game['toi_minutes']) * 60

        # Get opponent logo URL
        opponent_abbrev = game['opponent_abbrev']
        opponent_logo_row = team_logos[team_logos['team_abbrev'] == opponent_abbrev]
        opponent_logo_url = opponent_logo_row.iloc[0]['logo_url'] if len(opponent_logo_row) > 0 else ""

        games.append(
            PlayerGame(
                game_date=game['game_date'].strftime('%Y-%m-%d'),
                opponent=opponent_abbrev,
                opponent_logo_url=opponent_logo_url,
                home_away=home_away,
                shots=int(game['shots']),
                goals=int(game['goals']),
                assists=int(game['assists']),
                points=int(game['points']),
                toi_seconds=toi_seconds,
                game_id=int(game['game_id']) if pd.notna(game.get('game_id')) else None,
            )
        )

    # Calculate averages (toi_minutes is already in minutes)
    averages = {
        'shots_per_game': round(player_games['shots'].mean(), 2),
        'goals_per_game': round(player_games['goals'].mean(), 2),
        'assists_per_game': round(player_games['assists'].mean(), 2),
        'points_per_game': round(player_games['points'].mean(), 2),
        'toi_per_game': round(player_games['toi_minutes'].mean(), 2),
    }

    return PlayerGamesResponse(
        player_id=player_id,
        player_name=player_name,
        team=player_team,
        headshot_url=headshot_url,
        team_logo_url=team_logo_url,
        primary_color=primary_color,
        secondary_color=secondary_color,
        games_count=len(games),
        games=games,
        averages=averages,
    )


@router.get("/{player_id}/predictions", response_model=PlayerPredictionsResponse)
async def get_player_predictions(
    player_id: int,
    api_key: str = Depends(verify_api_key),
):
    """
    Get all predictions (upcoming and historical) for a specific player.

    Args:
        player_id: NHL player ID
        api_key: API key from header (required)

    Returns:
        PlayerPredictionsResponse: Player's upcoming and historical predictions
    """
    df = load_predictions()

    # Filter for this player
    player_predictions = df[df['player_id'] == player_id].copy()

    if len(player_predictions) == 0:
        raise HTTPException(status_code=404, detail=f"No predictions found for player ID {player_id}")

    # Get player info
    player_name = player_predictions.iloc[0]['player_name']

    # Separate upcoming vs historical (verified)
    now = datetime.now()
    player_predictions['game_date'] = player_predictions['game_time'].dt.tz_convert('America/New_York').dt.date

    upcoming = player_predictions[
        player_predictions['game_date'] >= now.date()
    ].sort_values('game_time')

    historical = player_predictions[
        (player_predictions['game_date'] < now.date()) |
        (player_predictions['result'].notna() & (player_predictions['result'] != 'UNKNOWN'))
    ].sort_values('game_time', ascending=False)

    # Convert to Prediction models with proper data conversions
    def convert_row_to_prediction(row):
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

        return Prediction(**row_dict)

    upcoming_predictions = [
        convert_row_to_prediction(row)
        for _, row in upcoming.iterrows()
    ]

    historical_predictions = [
        convert_row_to_prediction(row)
        for _, row in historical.iterrows()
    ]

    return PlayerPredictionsResponse(
        player_id=player_id,
        player_name=player_name,
        upcoming_count=len(upcoming_predictions),
        historical_count=len(historical_predictions),
        upcoming=upcoming_predictions,
        historical=historical_predictions,
    )