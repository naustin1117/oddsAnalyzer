"""
Verify Predictions Against Actual Results

This script:
1. Loads HIGH confidence predictions from predictions_history.csv
2. Fetches actual game results from NHL API
3. Determines if bets won/lost/pushed
4. Saves results to predictions_results.csv
"""

import pandas as pd
from datetime import datetime, timedelta, timezone
import requests
from nhl_api import NHLAPIClient


def get_recent_predictions(confidence='HIGH', days_ago=1):
    """
    Get predictions made N days ago with specific confidence level.

    Args:
        confidence (str): Confidence level to filter (HIGH, MEDIUM, LOW)
        days_ago (int): How many days back to check (default: 1 = yesterday)

    Returns:
        DataFrame: Filtered predictions with Poisson-based true edge
    """
    predictions_file = 'data/predictions_history_v2.csv'

    try:
        df = pd.read_csv(predictions_file)
    except FileNotFoundError:
        print(f"ERROR: {predictions_file} not found")
        return pd.DataFrame()

    # Filter for confidence level
    df_filtered = df[df['confidence'] == confidence].copy()

    # Convert prediction_date to datetime and extract date
    df_filtered['prediction_date'] = pd.to_datetime(df_filtered['prediction_date'])
    df_filtered['pred_date'] = df_filtered['prediction_date'].dt.date

    # Get the target date (N days ago) - use local time, not UTC
    target_date = (datetime.now() - timedelta(days=days_ago)).date()

    # Filter for predictions made on that specific date
    df_filtered = df_filtered[df_filtered['pred_date'] == target_date]

    print(f"Found {len(df_filtered)} {confidence} confidence predictions from {target_date}")

    return df_filtered


def get_nhl_game_id(game_date, away_team, home_team):
    """
    Get NHL game ID from schedule for a specific game.

    Args:
        game_date (str): Game date in YYYY-MM-DD format
        away_team (str): Away team name
        home_team (str): Home team name

    Returns:
        int or None: NHL game ID, or None if not found
    """
    try:
        # Fetch schedule for the date
        url = f"https://api-web.nhle.com/v1/schedule/{game_date}"
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return None

        data = response.json()
        game_week = data.get('gameWeek', [])

        # Search through all days in the week
        for day in game_week:
            for game in day.get('games', []):
                game_away = game.get('awayTeam', {}).get('placeName', {}).get('default', '')
                game_home = game.get('homeTeam', {}).get('placeName', {}).get('default', '')

                # Match by team names (partial match to handle name variations)
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
        # Fetch boxscore for the game
        url = f"https://api-web.nhle.com/v1/gamecenter/{nhl_game_id}/boxscore"
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return None

        data = response.json()

        # Get playerByGameStats
        player_stats = data.get('playerByGameStats', {})

        # Search through both teams' players
        for team_key in ['awayTeam', 'homeTeam']:
            team_data = player_stats.get(team_key, {})

            # Check forwards and defense
            for position in ['forwards', 'defense']:
                for player in team_data.get(position, []):
                    if player.get('playerId') == player_id:
                        return player.get('sog', 0)

        return None

    except Exception as e:
        print(f"    Error fetching shots for player {player_id}: {e}")
        return None


def calculate_units_won(odds_str, result):
    """
    Calculate units won/lost based on American odds.

    Args:
        odds_str (str or int): American odds (e.g., '-154' or '+120')
        result (str): 'WIN', 'LOSS', or 'PUSH'

    Returns:
        float: Units won (positive) or lost (negative)
    """
    if result == 'PUSH' or result == 'UNKNOWN':
        return 0.0

    if result == 'LOSS':
        return -1.0

    # WIN - calculate profit based on odds
    try:
        odds = int(odds_str)

        if odds > 0:
            # Positive odds (e.g., +120)
            # Profit = stake * (odds / 100)
            profit = 1.0 * (odds / 100.0)
        else:
            # Negative odds (e.g., -154)
            # Profit = stake * (100 / abs(odds))
            profit = 1.0 * (100.0 / abs(odds))

        return profit

    except (ValueError, TypeError):
        return 0.0


def check_prediction_result(recommendation, line, actual_shots, over_odds, under_odds):
    """
    Determine if a prediction won, lost, or pushed, and calculate units won.

    Args:
        recommendation (str): e.g., "BET OVER 2.5" or "BET UNDER 2.5"
        line (float): The betting line
        actual_shots (int): Actual shots in the game
        over_odds (str/int): Odds for over bet
        under_odds (str/int): Odds for under bet

    Returns:
        tuple: (result_str, units_won)
            result_str: 'WIN', 'LOSS', 'PUSH', or 'UNKNOWN'
            units_won: float (positive for profit, negative for loss)
    """
    if actual_shots is None:
        return 'UNKNOWN', 0.0

    # Determine which odds to use
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

    # Calculate units won
    units = calculate_units_won(relevant_odds, result)

    return result, units


def verify_predictions(confidence='HIGH', days_ago=1):
    """
    Main function to verify predictions against actual results.

    Args:
        confidence (str): Confidence level to check (HIGH, MEDIUM, LOW)
        days_ago (int): How many days back to check (1 = yesterday)

    Returns:
        DataFrame: Verified predictions with results
    """
    print("="*80)
    print("VERIFYING PREDICTIONS AGAINST ACTUAL RESULTS")
    print("="*80)
    print(f"Confidence level: {confidence}")
    print(f"Checking predictions from: {days_ago} day(s) ago")
    print()

    # Step 1: Get recent predictions
    print("Step 1: Loading predictions...")
    print("-"*80)

    predictions = get_recent_predictions(confidence, days_ago)

    if len(predictions) == 0:
        print(f"No {confidence} confidence predictions found from {days_ago} day(s) ago")
        return pd.DataFrame()

    # Display predictions to verify
    print(f"\nGames to verify:")
    for game in predictions[['game_time', 'away_team', 'home_team']].drop_duplicates().values:
        print(f"  {game[1]} @ {game[2]} ({game[0]})")

    # Step 2: Fetch actual results
    print("\nStep 2: Fetching actual game results...")
    print("-"*80)

    results = []
    nhl_game_id_cache = {}  # Cache game IDs to avoid redundant API calls

    for idx, pred in predictions.iterrows():
        player_name = pred['player_name']
        player_id = pred['player_id']

        # Convert game_time from UTC to EST to get the correct schedule date
        game_time_utc = pd.to_datetime(pred['game_time'])
        game_time_est = game_time_utc.tz_convert('America/New_York')
        game_date = game_time_est.strftime('%Y-%m-%d')

        away_team = pred['away_team']
        home_team = pred['home_team']
        line = pred['line']
        recommendation = pred['recommendation']

        print(f"  Checking {player_name} ({game_date})...", end=' ')

        # Get NHL game ID (use cache if available)
        game_key = f"{game_date}_{away_team}_{home_team}"
        if game_key not in nhl_game_id_cache:
            nhl_game_id = get_nhl_game_id(game_date, away_team, home_team)
            nhl_game_id_cache[game_key] = nhl_game_id
        else:
            nhl_game_id = nhl_game_id_cache[game_key]

        # Get actual shots from boxscore
        if nhl_game_id is None:
            print("⚠️  Game not found")
            actual_shots = None
        else:
            actual_shots = get_actual_shots(int(player_id), nhl_game_id)

        if actual_shots is None:
            print("⚠️  No data found")
            result_status = 'UNKNOWN'
            units_won = 0.0
        else:
            # Determine result and units won
            result_status, units_won = check_prediction_result(
                recommendation, line, actual_shots,
                pred['over_odds'], pred['under_odds']
            )

            if result_status == 'WIN':
                print(f"✓ {actual_shots} shots - WIN (+{units_won:.2f}u)")
            elif result_status == 'LOSS':
                print(f"✗ {actual_shots} shots - LOSS ({units_won:.2f}u)")
            else:
                print(f"≈ {actual_shots} shots - PUSH ({units_won:.2f}u)")

        # Store result
        results.append({
            'game_id': pred['game_id'],
            'game_time': pred['game_time'],
            'away_team': pred['away_team'],
            'home_team': pred['home_team'],
            'prediction_date': pred['prediction_date'],
            'player_name': player_name,
            'player_id': player_id,
            'team': pred['team'],
            'home_away': pred['home_away'],
            'line': line,
            'over_odds': pred['over_odds'],
            'under_odds': pred['under_odds'],
            'prediction': pred['prediction'],
            'difference': pred['difference'],
            'confidence': pred['confidence'],
            'true_edge': pred['true_edge'],
            'model_probability': pred.get('model_probability', None),
            'implied_probability': pred.get('implied_probability', None),
            'recommendation': recommendation,
            'bookmaker': pred['bookmaker'],
            'actual_shots': actual_shots,
            'result': result_status,
            'units_won': units_won
        })

    # Step 3: Save results
    print("\nStep 3: Saving results...")
    print("-"*80)

    results_df = pd.DataFrame(results)

    # Save to predictions_results.csv
    results_file = 'data/predictions_results.csv'
    results_df.to_csv(results_file, index=False)
    print(f"✓ Saved {len(results_df)} verified predictions to {results_file}")

    # Step 4: Calculate statistics
    print("\n" + "="*80)
    print("RESULTS SUMMARY")
    print("="*80)

    valid_results = results_df[results_df['result'] != 'UNKNOWN']

    if len(valid_results) == 0:
        print("\n⚠️  No valid results found (games may not have been played yet)")
        return results_df

    wins = (valid_results['result'] == 'WIN').sum()
    losses = (valid_results['result'] == 'LOSS').sum()
    pushes = (valid_results['result'] == 'PUSH').sum()

    total = len(valid_results)
    win_rate = (wins / total * 100) if total > 0 else 0

    # Calculate total units
    total_units = valid_results['units_won'].sum()
    avg_units_per_bet = total_units / total if total > 0 else 0

    print(f"\nTotal verified: {total}")
    print(f"Wins:   {wins} ({wins/total*100:.1f}%)")
    print(f"Losses: {losses} ({losses/total*100:.1f}%)")
    print(f"Pushes: {pushes} ({pushes/total*100:.1f}%)")

    print(f"\nWin Rate: {win_rate:.1f}%")

    print(f"\nUnits:")
    print(f"  Total: {total_units:+.2f}u")
    print(f"  Per bet: {avg_units_per_bet:+.2f}u")
    print(f"  ROI: {(total_units / total * 100):+.1f}%" if total > 0 else "  ROI: N/A")

    # Break-even analysis
    breakeven_rate = 52.4  # Need 52.4% to beat -110 vig
    if total_units > 0:
        print(f"\n✓ PROFITABLE! (+{total_units:.2f} units)")
    elif total_units < 0:
        print(f"\n✗ LOSING ({total_units:.2f} units)")
    else:
        print(f"\n≈ BREAK EVEN (0.00 units)")

    # Show wins and losses with true edge
    if wins > 0:
        print(f"\n{'='*80}")
        print("WINNING BETS")
        print("="*80)
        winning_bets = valid_results[valid_results['result'] == 'WIN']
        print(winning_bets[['player_name', 'line', 'prediction', 'actual_shots', 'true_edge', 'recommendation']].to_string(index=False))

    if losses > 0:
        print(f"\n{'='*80}")
        print("LOSING BETS")
        print("="*80)
        losing_bets = valid_results[valid_results['result'] == 'LOSS']
        print(losing_bets[['player_name', 'line', 'prediction', 'actual_shots', 'true_edge', 'recommendation']].to_string(index=False))

    print("\n" + "="*80)
    print("VERIFICATION COMPLETE")
    print("="*80)

    return results_df


if __name__ == "__main__":
    import sys

    # Default to HIGH confidence and yesterday's predictions
    confidence = 'HIGH'
    days_ago = 1

    # Allow command line arguments
    if len(sys.argv) > 1:
        confidence = sys.argv[1]
    if len(sys.argv) > 2:
        days_ago = int(sys.argv[2])

    # Run verification
    results = verify_predictions(confidence, days_ago)

    if len(results) > 0:
        print(f"\nResults saved to: data/predictions_results.csv")
        print("\nTo verify other confidence levels or dates:")
        print(f"  python3 verify_predictions.py MEDIUM 1   # Medium confidence, yesterday")
        print(f"  python3 verify_predictions.py HIGH 2     # High confidence, 2 days ago")