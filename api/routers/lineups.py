"""
Lineup endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
import pandas as pd
from pathlib import Path

from ..auth import verify_api_key
from ..models import LineupPlayer, TeamLineup, LineupsResponse
from ..services.data_loader import load_team_logos, load_player_name_mapping

router = APIRouter(prefix="/lineups", tags=["Lineups"])

# NHL team abbreviation to dailyfaceoff slug mapping
NHL_TEAM_MAPPING = {
    'ANA': 'anaheim-ducks',
    'BOS': 'boston-bruins',
    'BUF': 'buffalo-sabres',
    'CGY': 'calgary-flames',
    'CAR': 'carolina-hurricanes',
    'CHI': 'chicago-blackhawks',
    'COL': 'colorado-avalanche',
    'CBJ': 'columbus-blue-jackets',
    'DAL': 'dallas-stars',
    'DET': 'detroit-red-wings',
    'EDM': 'edmonton-oilers',
    'FLA': 'florida-panthers',
    'LAK': 'los-angeles-kings',
    'MIN': 'minnesota-wild',
    'MTL': 'montreal-canadiens',
    'NSH': 'nashville-predators',
    'NJD': 'new-jersey-devils',
    'NYI': 'new-york-islanders',
    'NYR': 'new-york-rangers',
    'OTT': 'ottawa-senators',
    'PHI': 'philadelphia-flyers',
    'PIT': 'pittsburgh-penguins',
    'SJS': 'san-jose-sharks',
    'SEA': 'seattle-kraken',
    'STL': 'st-louis-blues',
    'TBL': 'tampa-bay-lightning',
    'TOR': 'toronto-maple-leafs',
    'VAN': 'vancouver-canucks',
    'VGK': 'vegas-golden-knights',
    'WSH': 'washington-capitals',
    'WPG': 'winnipeg-jets',
    'UTA': 'utah-hockey-club'
}

# Reverse mapping: slug to abbreviation
SLUG_TO_ABBREV = {v: k for k, v in NHL_TEAM_MAPPING.items()}


def slug_to_name(slug: str) -> str:
    """Convert team slug to display name."""
    return slug.replace('-', ' ').title()


def load_lineup_data():
    """Load lineup data from CSV files."""
    base_path = Path(__file__).parent.parent.parent / "data"

    lines_file = base_path / "lineup_lines.csv"
    goalies_file = base_path / "lineup_goalies.csv"
    injuries_file = base_path / "lineup_injuries.csv"

    # Check if files exist
    if not lines_file.exists():
        raise FileNotFoundError(f"Lineup data not found at {lines_file}")

    # Load data
    df_lines = pd.read_csv(lines_file) if lines_file.exists() else pd.DataFrame()
    df_goalies = pd.read_csv(goalies_file) if goalies_file.exists() else pd.DataFrame()
    df_injuries = pd.read_csv(injuries_file) if injuries_file.exists() else pd.DataFrame()

    return df_lines, df_goalies, df_injuries


def get_team_lineup(team_slug: str, df_lines: pd.DataFrame, df_goalies: pd.DataFrame, df_injuries: pd.DataFrame, player_mapping: pd.DataFrame) -> TeamLineup:
    """Extract lineup for a specific team."""
    # Filter data for this team
    team_lines = df_lines[df_lines['team'] == team_slug]
    team_goalies = df_goalies[df_goalies['team'] == team_slug]
    team_injuries = df_injuries[df_injuries['team'] == team_slug]

    # Get opponent from the first row (should be the same for all players)
    opponent_slug = None
    if len(team_lines) > 0:
        opponent_slug = team_lines.iloc[0].get('opponent', None)
        if pd.isna(opponent_slug) or opponent_slug == '':
            opponent_slug = None

    # Get team abbreviation and look up team colors/logo
    team_abbrev = SLUG_TO_ABBREV.get(team_slug, '')
    team_logos = load_team_logos()
    team_logo_row = team_logos[team_logos['team_abbrev'] == team_abbrev]

    if len(team_logo_row) > 0:
        team_logo_url = team_logo_row.iloc[0]['logo_url']
        primary_color = team_logo_row.iloc[0]['primary_color']
        secondary_color = team_logo_row.iloc[0]['secondary_color']
    else:
        team_logo_url = ""
        primary_color = "#000000"
        secondary_color = "#FFFFFF"

    # Helper function to get headshot URL for a player
    def get_headshot_url(player_name: str) -> str:
        player_row = player_mapping[player_mapping['player_name'] == player_name]
        if len(player_row) > 0:
            return player_row.iloc[0]['headshot_url']
        return ""

    # Convert to LineupPlayer models
    line_combinations = []
    for _, player in team_lines.iterrows():
        line_combinations.append(
            LineupPlayer(
                player_name=player['player_name'],
                position=player['position'],
                position_id=player['position_id'],
                line=player['line'],
                line_id=player['line_id'],
                jersey_number=float(player['jersey_number']) if pd.notna(player.get('jersey_number')) else None,
                headshot_url=get_headshot_url(player['player_name']),
                injury_status=player.get('injury_status', None) if pd.notna(player.get('injury_status')) else None,
                game_time_decision=bool(player.get('game_time_decision', False)) if pd.notna(player.get('game_time_decision')) else None,
            )
        )

    goalies = []
    for _, player in team_goalies.iterrows():
        goalies.append(
            LineupPlayer(
                player_name=player['player_name'],
                position=player['position'],
                position_id=player['position_id'],
                line=player['line'],
                line_id=player['line_id'],
                jersey_number=float(player['jersey_number']) if pd.notna(player.get('jersey_number')) else None,
                headshot_url=get_headshot_url(player['player_name']),
                injury_status=player.get('injury_status', None) if pd.notna(player.get('injury_status')) else None,
                game_time_decision=bool(player.get('game_time_decision', False)) if pd.notna(player.get('game_time_decision')) else None,
            )
        )

    injuries = []
    for _, player in team_injuries.iterrows():
        injuries.append(
            LineupPlayer(
                player_name=player['player_name'],
                position=player['position'],
                position_id=player['position_id'],
                line=player['line'],
                line_id=player['line_id'],
                jersey_number=float(player['jersey_number']) if pd.notna(player.get('jersey_number')) else None,
                headshot_url=get_headshot_url(player['player_name']),
                injury_status=player.get('injury_status', None) if pd.notna(player.get('injury_status')) else None,
                game_time_decision=bool(player.get('game_time_decision', False)) if pd.notna(player.get('game_time_decision')) else None,
            )
        )

    return TeamLineup(
        team=team_slug,
        team_name=slug_to_name(team_slug),
        team_logo_url=team_logo_url,
        primary_color=primary_color,
        secondary_color=secondary_color,
        opponent=opponent_slug,
        opponent_name=slug_to_name(opponent_slug) if opponent_slug else None,
        line_combinations=line_combinations,
        goalies=goalies,
        injuries=injuries,
    )


@router.get("/{team_abbrev}", response_model=LineupsResponse)
async def get_lineups(
    team_abbrev: str,
    api_key: str = Depends(verify_api_key),
):
    """
    Get lineup information for a team and their opponent.

    Args:
        team_abbrev: NHL team abbreviation (e.g., 'BOS', 'FLA', 'CHI')
        api_key: API key from header (required)

    Returns:
        LineupsResponse: Lineups for the requested team and their opponent
    """
    # Normalize team abbreviation to uppercase
    team_abbrev = team_abbrev.upper()

    # Validate team abbreviation
    if team_abbrev not in NHL_TEAM_MAPPING:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid team abbreviation: {team_abbrev}. Must be one of: {', '.join(sorted(NHL_TEAM_MAPPING.keys()))}"
        )

    # Get team slug
    team_slug = NHL_TEAM_MAPPING[team_abbrev]

    # Load lineup data
    try:
        df_lines, df_goalies, df_injuries = load_lineup_data()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Load player name mapping for headshots
    player_mapping = load_player_name_mapping()

    # Check if team has lineup data
    if len(df_lines[df_lines['team'] == team_slug]) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No lineup data found for {team_abbrev}. The team may not be playing today or lineups haven't been scraped yet."
        )

    # Get team lineup
    team_lineup = get_team_lineup(team_slug, df_lines, df_goalies, df_injuries, player_mapping)

    # Get opponent lineup if opponent exists
    opponent_lineup = None
    if team_lineup.opponent:
        opponent_lineup = get_team_lineup(team_lineup.opponent, df_lines, df_goalies, df_injuries, player_mapping)

    return LineupsResponse(
        team=team_lineup,
        opponent=opponent_lineup,
    )