"""
Generate AI summaries for HIGH confidence predictions.

This script:
1. Loads today's predictions
2. Filters for HIGH confidence only
3. Generates AI summaries using Groq
4. Updates the predictions CSV with summaries
"""

import sys
from pathlib import Path

# Add parent directory to path to import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import os
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import existing data loaders
from api.services.data_loader import load_predictions, load_player_logs

PREDICTIONS_FILE = 'data/predictions_history_v2.csv'


def get_groq_api_key() -> str:
    """Get Groq API key from environment"""
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")
    return api_key


def build_summary_prompt(
    prediction_row: pd.Series,
    best_avg: float,
    avg_label: str,
    season_avg: float,
    season_hit_rate: float = None,
    season_hit_side: str = None,
    season_games: int = None,
) -> str:
    """Build prompt for AI summary generation"""

    # Determine opponent
    opponent = prediction_row['away_team'] if prediction_row['team'] in str(prediction_row['home_team']) else prediction_row['home_team']
    is_over = 'OVER' in str(prediction_row['recommendation']).upper()

    player = prediction_row['player_name']
    team = prediction_row['team']
    line = float(prediction_row['line'])
    pred = float(prediction_row['prediction'])
    edge_pct = float(prediction_row.get('true_edge', 0) or 0)

    # Derived helpers
    model_delta = pred - line
    recent_delta = best_avg - line
    season_delta = season_avg - line

    direction = "OVER" if is_over else "UNDER"
    tone_rule = "positive" if is_over else "negative"

    # Optional hit-rate sentence fragment
    hit_rate_fragment = ""
    if season_hit_rate is not None and season_hit_side is not None:
        pct = season_hit_rate * 100.0
        if season_games is not None and season_games > 0:
            hit_rate_fragment = f"{season_hit_side.title()} {line:g} in {pct:.0f}% of games this season ({season_games}g)."
        else:
            hit_rate_fragment = f"{season_hit_side.title()} {line:g} in {pct:.0f}% of games this season."

    prompt = f"""
You write NHL shots-on-goal betting notes. Output should be 2–3 sentences, max 50 words.
Write in natural, flowing sentences with proper grammar. Be specific and provide context.

Hard bans:
- Do NOT say: "good bet", "great bet", "value play", "lock", "slam", "hammer", "must", "guarantee", "can't miss".
- Do NOT mention "high confidence" or talk about "selling" the pick.
- No emojis.
- Do NOT use team name as the subject. This is a PLAYER prop bet.
- Do NOT use colons (:) to separate clauses. Write in complete sentences.

Requirements:
- MUST use the player's name as the subject (e.g., "{player} under {line:g}" NOT "The {team} under {line:g}").
- Write naturally: "{player} under {line:g} has a 68% hit rate" NOT "{player} under {line:g}: 68% hit rate"
- Include at least TWO numbers chosen from: recent avg, season avg, model projection, model-vs-line delta, hit rate %, edge%.
- Prefer SHOTS delta (projection - line) over % edge when possible.
- If hit rate is provided, try to use it (especially for UNDERs) as the lead stat.
- Tone must be {tone_rule}: OVER = strong form/volume; UNDER = cooled off/low volume.

Data:
- Player: {player} ({team}) vs {opponent}
- Pick: {direction} {line:g}
- Model projection: {pred:.1f} SOG (delta vs line: {model_delta:+.1f})
- Recent form: {best_avg:.1f} SOG/game ({avg_label}) (delta vs line: {recent_delta:+.1f})
- Season avg: {season_avg:.1f} SOG/game (delta vs line: {season_delta:+.1f})
- Edge: {edge_pct:.1f}%
- Season hit rate (optional): {hit_rate_fragment if hit_rate_fragment else "N/A"}

Writing guidance:
- Start with PLAYER NAME and pick, then add supporting evidence.
- Use action verbs: "has", "posts", "averages", "projects to"
- Example good structure: "{player} under {line:g} has hit in 68% of games, posting just 2.4 SOG/game recently."
- Avoid repeating the player name twice.
- No filler like "tonight", "I like", "we love".

Return ONLY the summary text.
""".strip()

    return prompt


def call_groq_api(prompt: str, api_key: str) -> str:
    """Call Groq API to generate summary"""

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "system",
                "content": "You are a sports betting analyst. Keep responses under 50 words but be specific and provide context."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.8,
        "max_tokens": 150,
        "top_p": 1,
        "stream": False
    }

    response = requests.post(url, json=payload, headers=headers, timeout=10)
    response.raise_for_status()

    result = response.json()
    summary = result['choices'][0]['message']['content'].strip()

    # Remove quotes if AI wrapped the response
    if summary.startswith('"') and summary.endswith('"'):
        summary = summary[1:-1]
    if summary.startswith("'") and summary.endswith("'"):
        summary = summary[1:-1]

    return summary


def generate_summaries_for_high_confidence():
    """
    Main function to generate AI summaries for all HIGH confidence predictions.
    """

    print("🤖 Starting AI summary generation...")

    # Get API key
    try:
        api_key = get_groq_api_key()
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("Please set GROQ_API_KEY environment variable:")
        print("  export GROQ_API_KEY=your_key_here")
        return

    # Load predictions
    print("📊 Loading predictions...")
    df = pd.read_csv(PREDICTIONS_FILE)
    df['game_time'] = pd.to_datetime(df['game_time'])

    # Get today's date (EST)
    from datetime import datetime, timezone
    import pytz
    est = pytz.timezone('America/New_York')
    today = datetime.now(est).date()

    # Filter for today's HIGH confidence predictions
    df['game_date_only'] = df['game_time'].dt.tz_convert('America/New_York').dt.date
    todays_high = df[
        (df['game_date_only'] == today) &
        (df['confidence'] == 'HIGH')
    ].copy()

    if len(todays_high) == 0:
        print("✅ No HIGH confidence predictions found for today")
        return

    print(f"Found {len(todays_high)} HIGH confidence predictions")

    # Load player logs for recent stats
    print("📈 Loading player stats...")
    player_logs = load_player_logs()

    # Generate summaries
    summaries_generated = 0

    for idx, row in todays_high.iterrows():
        player_id = row['player_id']
        line = float(row['line'])

        # Get player's recent performance
        player_games = player_logs[player_logs['player_id'] == player_id].copy()

        if len(player_games) > 0:
            player_games = player_games.sort_values('game_date', ascending=False)
            last_5_avg = player_games.head(5)['shots'].mean()
            last_10_avg = player_games.head(10)['shots'].mean()
            season_avg = player_games['shots'].mean()

            # Pick the best average based on recommendation
            # For OVER picks: use the highest average (most bullish)
            # For UNDER picks: use the lowest average (most bearish)
            averages = [
                (last_5_avg, 'last 5 games', 'L5'),
                (last_10_avg, 'last 10 games', 'L10'),
                (season_avg, 'this season', 'Season')
            ]

            if 'OVER' in row['recommendation']:
                best_avg, avg_label, time_filter = max(averages, key=lambda x: x[0])
            else:  # UNDER
                best_avg, avg_label, time_filter = min(averages, key=lambda x: x[0])

            # Calculate season hit rate for this line
            season_games = len(player_games)
            over_count = (player_games['shots'] > line).sum()
            under_count = (player_games['shots'] < line).sum()

            # Determine which side hit more often
            if over_count > under_count:
                season_hit_side = "OVER"
                season_hit_rate = over_count / season_games if season_games > 0 else None
            elif under_count > over_count:
                season_hit_side = "UNDER"
                season_hit_rate = under_count / season_games if season_games > 0 else None
            else:
                # Tie or equal - use the recommendation side
                season_hit_side = "OVER" if 'OVER' in row['recommendation'] else "UNDER"
                season_hit_rate = 0.5
        else:
            best_avg = row['prediction']
            avg_label = 'recent games'
            season_avg = row['prediction']
            season_hit_rate = None
            season_hit_side = None
            season_games = None
            time_filter = 'Season'  # Default to season if no data

        # Build prompt
        prompt = build_summary_prompt(
            row,
            best_avg,
            avg_label,
            season_avg,
            season_hit_rate=season_hit_rate,
            season_hit_side=season_hit_side,
            season_games=season_games
        )

        try:
            # Call Groq API
            print(f"  Generating summary for {row['player_name']}...")
            summary = call_groq_api(prompt, api_key)

            # Update dataframe
            df.at[idx, 'ai_summary'] = summary
            df.at[idx, 'suggested_time_filter'] = time_filter
            summaries_generated += 1

            # Rate limit: small delay between requests
            time.sleep(0.5)

        except Exception as e:
            print(f"  ❌ Error generating summary for {row['player_name']}: {e}")
            df.at[idx, 'ai_summary'] = None

    # Save updated predictions
    if summaries_generated > 0:
        print(f"\n💾 Saving {summaries_generated} summaries to CSV...")
        df.to_csv(PREDICTIONS_FILE, index=False)
        print(f"✅ Done! Generated {summaries_generated} AI summaries")
    else:
        print("⚠️  No summaries generated")


if __name__ == '__main__':
    generate_summaries_for_high_confidence()
