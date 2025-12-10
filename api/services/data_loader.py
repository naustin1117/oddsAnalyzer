"""
Data loading service for predictions and player logs.
"""
from fastapi import HTTPException
import pandas as pd

from ..config import PREDICTIONS_FILE, PLAYER_LOGS_FILE, PLAYER_NAME_MAPPING_FILE, TEAM_LOGOS_FILE


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


def load_player_logs() -> pd.DataFrame:
    """Load player game logs from CSV file."""
    try:
        df = pd.read_csv(PLAYER_LOGS_FILE)
        return df
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Player logs file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading player logs: {str(e)}")


def load_player_name_mapping() -> pd.DataFrame:
    """Load player ID to name mapping from CSV file."""
    try:
        df = pd.read_csv(PLAYER_NAME_MAPPING_FILE)
        return df
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Player name mapping file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading player name mapping: {str(e)}")


def load_team_logos() -> pd.DataFrame:
    """Load team logos mapping from CSV file."""
    try:
        df = pd.read_csv(TEAM_LOGOS_FILE)
        return df
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Team logos file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading team logos: {str(e)}")