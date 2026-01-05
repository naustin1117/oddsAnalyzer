"""
API Configuration
"""
import os
from typing import Set

# API Keys - In production, store these in environment variables
API_KEYS: Set[str] = {
    os.getenv("API_KEY_1", "dev-key-123"),  # Default key for development
}

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")

# CORS Settings
ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React default
    "http://localhost:5173",  # Vite default
    "http://localhost:8080",  # Vue default
    "https://odds-analyzer-three.vercel.app",  # Production frontend (hardcoded fallback)
]

# Add production frontend URL from env if set
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url and frontend_url not in ALLOWED_ORIGINS:
    ALLOWED_ORIGINS.append(frontend_url)

# Debug: Print allowed origins on startup
print(f"🔒 CORS Allowed Origins: {ALLOWED_ORIGINS}")

# Data file paths
PREDICTIONS_FILE = "data/predictions_history_v2.csv"
PLAYER_LOGS_FILE = "data/player_game_logs_2025_2026_with_opponent.csv"
PLAYER_NAME_MAPPING_FILE = "data/player_name_to_id.csv"
TEAM_LOGOS_FILE = "data/team_logos.csv"
LINEUP_NEWS_FILE = "data/lineup_news.csv"