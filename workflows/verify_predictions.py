"""
Verify Predictions Against Actual Results

This script:
1. Loads unverified predictions from predictions_history_v2.csv
2. Fetches actual game results from NHL API using stored nhl_game_id
3. Determines if bets won/lost/pushed
4. Updates predictions_history_v2.csv with results
"""

import sys
from pathlib import Path

# Add parent directory to path to import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from datetime import datetime, timedelta
import requests


def get_unverified_predictions(days_ago=1):
    """
    Get unverified predictions from N days ago (all confidence levels).

    Args:
        days_ago (int): How many days back to check (default: 1 = yesterday)

    Returns:
        DataFrame: Unverified predictions
    """
    predictions_file = 'data/predictions_history_v2.csv'

    try:
        df = pd.read_csv(predictions_file)
    except FileNotFoundError:
        print(f"ERROR: {predictions_file} not found")
        return pd.DataFrame()

    # Filter for unverified predictions (result is None or UNKNOWN)
    unverified = df[(df['result'].isna()) | (df['result'] == 'UNKNOWN')].copy()

    # Convert game_time to datetime
    unverified['game_time'] = pd.to_datetime(unverified['game_time'])

    # Get the target date (N days ago)
    target_date = (datetime.now() - timedelta(days=days_ago)).date()

    # Convert to EST timezone to match game dates
    unverified['game_date'] = unverified['game_time'].dt.tz_convert('America/New_York').dt.date

    # Filter for games from the target date
    unverified = unverified[unverified['game_date'] == target_date]

    print(f"Found {len(unverified)} unverified predictions from {target_date}")

    return unverified


def get_nhl_game_id_from_schedule(game_date, away_team, home_team):
    """
    Get NHL game ID from schedule (fallback for old predictions without nhl_game_id).

    Args:
        game_date (str): Game date in YYYY-MM-DD format
        away_team (str): Away team name
        home_team (str): Home team name

    Returns:
        int or None: NHL game ID, or None if not found
    """
    try:
        url = f"https://api-web.nhle.com/v1/schedule/{game_date}"
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return None

        data = response.json()

        for day in data.get('gameWeek', []):
            for game in day.get('games', []):
                game_away = game.get('awayTeam', {}).get('placeName', {}).get('default', '')
                game_home = game.get('homeTeam', {}).get('placeName', {}).get('default', '')

                if away_team in game_away or game_away in away_team:
                    if home_team in game_home or game_home in home_team:
                        return game.get('id')

        return None

    except Exception as e:
        print(f"    Error fetching game ID: {e}")
        return None


def get_actual_shots(player_id, nhl_game_id):
    """
    Get actual shots for a player in a specific game from NHL boxscore.

    Args:
        player_id (int): NHL player ID
        nhl_game_id (int): NHL game ID

    Returns:
        int or None: Actual shots on goal, or None if not found
    """
    try:
        url = f"https://api-web.nhle.com/v1/gamecenter/{nhl_game_id}/boxscore"
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return None

        data = response.json()
        player_stats = data.get('playerByGameStats', {})

        for team_key in ['awayTeam', 'homeTeam']:
            team_data = player_stats.get(team_key, {})

            for position in ['forwards', 'defense']:
                for player in team_data.get(position, []):
                    if player.get('playerId') == player_id:
                        return player.get('sog', 0)

        return None

    except Exception as e:
        print(f"    Error fetching shots: {e}")
        return None


def calculate_units_won(odds_str, result):
    """
    Calculate units won/lost based on American odds.

    Args:
        odds_str (str or int): American odds
        result (str): 'WIN', 'LOSS', or 'PUSH'

    Returns:
        float: Units won (positive) or lost (negative)
    """
    if result == 'PUSH' or result == 'UNKNOWN':
        return 0.0

    if result == 'LOSS':
        return -1.0

    try:
        odds = int(odds_str)

        if odds > 0:
            profit = 1.0 * (odds / 100.0)
        else:
            profit = 1.0 * (100.0 / abs(odds))

        return profit

    except (ValueError, TypeError):
        return 0.0


def check_prediction_result(recommendation, line, actual_shots, over_odds, under_odds):
    """
    Determine if a prediction won, lost, or pushed.

    Args:
        recommendation (str): e.g., "BET OVER 2.5"
        line (float): The betting line
        actual_shots (int): Actual shots in the game
        over_odds (str/int): Odds for over bet
        under_odds (str/int): Odds for under bet

    Returns:
        tuple: (result_str, units_won)
    """
    if actual_shots is None:
        return 'UNKNOWN', 0.0

    if 'OVER' in recommendation:
        relevant_odds = over_odds
        if actual_shots > line:
            result = 'WIN'
        elif actual_shots < line:
            result = 'LOSS'
        else:
            result = 'PUSH'
    elif 'UNDER' in recommendation:
        relevant_odds = under_odds
        if actual_shots < line:
            result = 'WIN'
        elif actual_shots > line:
            result = 'LOSS'
        else:
            result = 'PUSH'
    else:
        return 'UNKNOWN', 0.0

    units = calculate_units_won(relevant_odds, result)
    return result, units


def verify_predictions(days_ago=1):
    """
    Verify all unverified predictions from N days ago.

    Args:
        days_ago (int): How many days back to check (1 = yesterday)

    Returns:
        int: Number of predictions verified
    """
    print("="*80)
    print("VERIFYING PREDICTIONS AGAINST ACTUAL RESULTS")
    print("="*80)
    print(f"Checking predictions from: {days_ago} day(s) ago")
    print(f"Verifying: ALL CONFIDENCE LEVELS\n")

    # Step 1: Get unverified predictions
    print("Step 1: Loading unverified predictions...")
    print("-"*80)

    predictions = get_unverified_predictions(days_ago)

    if len(predictions) == 0:
        print(f"No unverified predictions found from {days_ago} day(s) ago")
        return 0

    # Display games to verify
    print(f"\nGames to verify:")
    for game in predictions[['game_time', 'away_team', 'home_team']].drop_duplicates().values:
        print(f"  {game[1]} @ {game[2]}")

    # Step 2: Load full predictions file for updating
    predictions_file = 'data/predictions_history_v2.csv'
    df_all = pd.read_csv(predictions_file)

    # Ensure nhl_game_id column exists
    if 'nhl_game_id' not in df_all.columns:
        df_all['nhl_game_id'] = None

    # Step 3: Fetch actual results
    print("\nStep 2: Fetching actual game results...")
    print("-"*80)

    verified_count = 0

    for idx, pred in predictions.iterrows():
        player_name = pred['player_name']
        player_id = int(pred['player_id'])
        game_date = pred['game_date'].strftime('%Y-%m-%d')

        print(f"  {player_name} ({game_date})...", end=' ')

        # Try to get NHL game ID from the row first (if stored)
        nhl_game_id = pred.get('nhl_game_id')

        if pd.notna(nhl_game_id):
            # Use stored NHL game ID
            nhl_game_id = int(nhl_game_id)
        else:
            # Fallback: look up from schedule
            print("(looking up NHL game ID)...", end=' ')
            nhl_game_id = get_nhl_game_id_from_schedule(
                game_date,
                pred['away_team'],
                pred['home_team']
            )

            # Store it for future use
            if nhl_game_id is not None:
                df_all.at[idx, 'nhl_game_id'] = nhl_game_id

        # Get actual shots
        if nhl_game_id is None:
            print("⚠️  Game not found")
            actual_shots = None
            result_status = 'UNKNOWN'
            units_won = 0.0
        else:
            actual_shots = get_actual_shots(player_id, nhl_game_id)

            if actual_shots is None:
                print("⚠️  No data found")
                result_status = 'UNKNOWN'
                units_won = 0.0
            else:
                result_status, units_won = check_prediction_result(
                    pred['recommendation'],
                    pred['line'],
                    actual_shots,
                    pred['over_odds'],
                    pred['under_odds']
                )

                if result_status == 'WIN':
                    print(f"✓ {actual_shots} shots - WIN (+{units_won:.2f}u)")
                elif result_status == 'LOSS':
                    print(f"✗ {actual_shots} shots - LOSS ({units_won:.2f}u)")
                else:
                    print(f"≈ {actual_shots} shots - PUSH")

        # Update the main dataframe
        df_all.at[idx, 'actual_shots'] = actual_shots
        df_all.at[idx, 'result'] = result_status
        df_all.at[idx, 'units_won'] = units_won

        if result_status != 'UNKNOWN':
            verified_count += 1

    # Step 4: Save updated predictions
    print("\nStep 3: Saving results...")
    print("-"*80)

    df_all.to_csv(predictions_file, index=False)
    print(f"✓ Updated {predictions_file} with {verified_count} verified predictions")

    # Step 5: Calculate statistics
    print("\n" + "="*80)
    print("RESULTS SUMMARY")
    print("="*80)

    verified = predictions[predictions['result'] != 'UNKNOWN']

    if verified_count == 0:
        print("\n⚠️  No valid results found (games may not have been played yet)")
        return 0

    # Re-read to get updated results
    updated_predictions = df_all.loc[predictions.index]
    valid_results = updated_predictions[updated_predictions['result'] != 'UNKNOWN']

    wins = (valid_results['result'] == 'WIN').sum()
    losses = (valid_results['result'] == 'LOSS').sum()
    pushes = (valid_results['result'] == 'PUSH').sum()
    total = len(valid_results)

    # Calculate units
    total_units = valid_results['units_won'].sum()

    print(f"\nTotal verified: {total}")
    print(f"  Wins:   {wins} ({wins/total*100:.1f}%)")
    print(f"  Losses: {losses} ({losses/total*100:.1f}%)")
    print(f"  Pushes: {pushes} ({pushes/total*100:.1f}%)")

    print(f"\nUnits:")
    print(f"  Total: {total_units:+.2f}u")
    print(f"  Per bet: {(total_units/total):+.2f}u" if total > 0 else "  Per bet: N/A")
    print(f"  ROI: {(total_units/total*100):+.1f}%" if total > 0 else "  ROI: N/A")

    # Breakdown by confidence
    print(f"\n{'='*80}")
    print("BREAKDOWN BY CONFIDENCE LEVEL")
    print("="*80)

    for conf in ['HIGH', 'MEDIUM', 'LOW']:
        conf_bets = valid_results[valid_results['confidence'] == conf]
        if len(conf_bets) > 0:
            conf_wins = (conf_bets['result'] == 'WIN').sum()
            conf_total = len(conf_bets)
            conf_units = conf_bets['units_won'].sum()
            print(f"\n{conf}: {conf_wins}/{conf_total} ({conf_wins/conf_total*100:.1f}%) - {conf_units:+.2f}u")

    print("\n" + "="*80)
    print("VERIFICATION COMPLETE")
    print("="*80)

    return verified_count


if __name__ == "__main__":
    # Default to yesterday's predictions
    days_ago = 1

    # Allow command line argument for days
    if len(sys.argv) > 1:
        days_ago = int(sys.argv[1])

    # Run verification
    verified = verify_predictions(days_ago)

    if verified > 0:
        print(f"\n✓ Results saved to: data/predictions_history_v2.csv")
        print(f"\nTo verify other dates:")
        print(f"  python workflows/verify_predictions.py 1  # Yesterday")
        print(f"  python workflows/verify_predictions.py 2  # 2 days ago")