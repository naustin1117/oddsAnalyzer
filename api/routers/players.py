"""
Player-specific endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime
import pandas as pd
import logging

from ..auth import verify_api_key
from ..models import (
    PlayerGame,
    PlayerGamesResponse,
    Prediction,
    PlayerPredictionsResponse,
    PlayerNewsItem,
    PlayerNewsResponse,
    BulkPlayerGamesRequest,
    BulkPlayerGamesResponse
)
from ..services.data_loader import load_predictions, load_player_logs, load_player_name_mapping, load_team_logos, load_player_news
from ..team_names import get_team_name, get_team_abbrev

router = APIRouter(prefix="/players", tags=["Players"])


@router.get("/{player_id}/recent-games", response_model=PlayerGamesResponse)
async def get_player_recent_games(
    player_id: int,
    limit: int = Query(10, ge=1, le=82, description="Number of recent games to fetch"),
    full_season: bool = Query(False, description="If true, returns all games from current season (ignores limit)"),
    api_key: str = Depends(verify_api_key),
):
    """
    Get a player's recent game-by-game statistics.

    Args:
        player_id: NHL player ID
        limit: Number of recent games (1-82, default 10)
        full_season: If True, returns all current season games
        api_key: API key from header (required)

    Returns:
        PlayerGamesResponse: Player's recent games with stats and averages
    """
    df = load_player_logs()

    # Filter for this player
    player_games = df[df['player_id'] == player_id].copy()

    if len(player_games) == 0:
        raise HTTPException(status_code=404, detail=f"No games found for player ID {player_id}")

    # Sort by date (most recent first)
    player_games['game_date'] = pd.to_datetime(player_games['game_date'])
    player_games = player_games.sort_values('game_date', ascending=False)

    # Apply limit unless full_season is requested
    if not full_season:
        player_games = player_games.head(limit)

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
        team_abbrev=player_team,
        team_name=get_team_name(player_team),
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
        player_team_abbrev = row_dict.pop('team', None)
        row_dict['player_team'] = player_team_abbrev
        row_dict['player_team_name'] = get_team_name(player_team_abbrev) if player_team_abbrev else None
        row_dict['model_prob'] = row_dict.pop('model_probability', None)
        row_dict['implied_prob'] = row_dict.pop('implied_probability', None)

        # Add team abbreviations (away_team and home_team are full names in CSV)
        away_team_name = row_dict.get('away_team')
        home_team_name = row_dict.get('home_team')
        row_dict['away_team_abbrev'] = get_team_abbrev(away_team_name) if away_team_name else None
        row_dict['home_team_abbrev'] = get_team_abbrev(home_team_name) if home_team_name else None

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


@router.get("/{player_id}/news", response_model=PlayerNewsResponse)
async def get_player_news(
    player_id: int,
    limit: int = Query(10, ge=1, le=50, description="Number of recent news items to fetch"),
    api_key: str = Depends(verify_api_key),
):
    """
    Get recent news for a specific player by player ID.

    Args:
        player_id: Player ID (e.g., 8478402)
        limit: Number of recent news items (1-50, default 10)
        api_key: API key from header (required)

    Returns:
        PlayerNewsResponse: Player's recent news items
    """
    df = load_player_news()

    # Filter for this player by player_id
    player_news = df[df['player_id'] == player_id].copy()

    if len(player_news) == 0:
        raise HTTPException(status_code=404, detail=f"No news found for player ID {player_id}")

    # Sort by created_at (most recent first) and limit
    player_news = player_news.sort_values('created_at', ascending=False).head(limit)

    # Get player_name from first record
    player_name = player_news.iloc[0]['player_name']

    # Convert to PlayerNewsItem models
    news_items = []
    for _, news in player_news.iterrows():
        news_items.append(
            PlayerNewsItem(
                team=news['team'],
                player_id=int(news['player_id']) if pd.notna(news.get('player_id')) else None,
                player_name=news['player_name'],
                created_at=news['created_at'].isoformat(),
                details=news['details'] if pd.notna(news['details']) else '',
                fantasy_details=news['fantasy_details'] if pd.notna(news['fantasy_details']) else '',
                scrape_date=news['scrape_date'],
            )
        )

    return PlayerNewsResponse(
        player_id=player_id,
        player_name=player_name,
        news_count=len(news_items),
        news=news_items,
    )


@router.post("/bulk/recent-games", response_model=BulkPlayerGamesResponse)
async def get_bulk_player_recent_games(
    request: BulkPlayerGamesRequest,
    api_key: str = Depends(verify_api_key),
):
    """
    Get recent game-by-game statistics for multiple players in a single request.

    Args:
        request: BulkPlayerGamesRequest containing player_ids and limit
        api_key: API key from header (required)

    Returns:
        BulkPlayerGamesResponse: Recent games for all requested players
    """
    # Load data once for all players
    df = load_player_logs()
    player_mapping = load_player_name_mapping()
    team_logos = load_team_logos()

    players_data = []

    for player_id in request.player_ids:
        try:
            # Filter for this player
            player_games = df[df['player_id'] == player_id].copy()

            if len(player_games) == 0:
                logging.warning(f"No games found for player ID {player_id}, skipping")
                continue

            # Sort by date (most recent first) and limit
            player_games['game_date'] = pd.to_datetime(player_games['game_date'])
            player_games = player_games.sort_values('game_date', ascending=False).head(request.limit)

            # Get player info from name mapping
            player_info = player_mapping[player_mapping['player_id'] == player_id]

            if len(player_info) == 0:
                logging.warning(f"Player name not found for player ID {player_id}, skipping")
                continue

            player_name = player_info.iloc[0]['player_name']
            headshot_url = player_info.iloc[0]['headshot_url']
            player_team = player_games.iloc[0]['team_abbrev']

            # Get team logo URL and colors
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

            players_data.append(
                PlayerGamesResponse(
                    player_id=player_id,
                    player_name=player_name,
                    team_abbrev=player_team,
                    team_name=get_team_name(player_team),
                    headshot_url=headshot_url,
                    team_logo_url=team_logo_url,
                    primary_color=primary_color,
                    secondary_color=secondary_color,
                    games_count=len(games),
                    games=games,
                    averages=averages,
                )
            )

        except Exception as e:
            logging.error(f"Error processing player ID {player_id}: {str(e)}")
            continue

    return BulkPlayerGamesResponse(
        count=len(players_data),
        players=players_data,
    )