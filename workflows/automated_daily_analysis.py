"""
Automated Daily NHL Betting Analysis

This script runs daily to:
1. Update player game logs with last night's games
2. Rebuild team stats and opponent features
3. Fetch today's NHL games
4. Pull FanDuel SOG lines for each game
5. Run model predictions with updated data
6. Calculate true edge using Poisson distribution
7. Save all predictions to predictions_history_v2.csv

Designed to run as a cron job.
"""

import sys
from pathlib import Path

# Add parent directory to path to import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from datetime import datetime
import os
import time
import numpy as np
from scipy.stats import poisson
from odds_api import OddsAPIClient
from simple_predict import predict_shots, get_model
from nhl_api import NHLAPIClient
from add_opponent_features import add_opponent_features


def odds_to_implied_prob(odds):
    """
    Convert American odds to implied probability.

    Args:
        odds (int): American odds (e.g., -180 or +150)

    Returns:
        float: Implied probability as decimal (0-1)
    """
    try:
        odds = int(odds)
        if odds > 0:
            # Positive odds: prob = 100 / (odds + 100)
            return 100.0 / (odds + 100.0)
        else:
            # Negative odds: prob = |odds| / (|odds| + 100)
            return abs(odds) / (abs(odds) + 100.0)
    except (ValueError, TypeError):
        return np.nan


def calculate_poisson_probability(prediction, line, bet_type):
    """
    Calculate probability of OVER or UNDER using Poisson distribution.

    Args:
        prediction (float): Model's predicted shots
        line (float): Betting line
        bet_type (str): 'OVER' or 'UNDER'

    Returns:
        float: Probability as decimal (0-1)
    """
    if bet_type == 'OVER':
        # P(X > line) = 1 - P(X <= line)
        return 1 - poisson.cdf(line, prediction)
    else:  # UNDER
        # P(X < line) = P(X <= line-1)
        # For 1.5 line: P(X < 1.5) = P(X <= 1) = P(X=0) + P(X=1)
        return poisson.cdf(line - 0.5, prediction)


def load_player_mapping():
    """
    Load player name to ID mapping.

    Returns:
        dict: Player name -> player ID mapping
    """
    mapping_file = 'data/player_name_to_id.csv'

    if not os.path.exists(mapping_file):
        raise FileNotFoundError(
            f"Player mapping file not found at {mapping_file}. "
            "Run create_player_mapping.py first."
        )

    mapping_df = pd.read_csv(mapping_file)
    mapping = dict(zip(mapping_df['player_name'], mapping_df['player_id']))
    print(f"✓ Loaded {len(mapping)} player mappings")
    return mapping


def get_todays_games(client):
    """
    Fetch today's NHL games from The Odds API.

    Args:
        client (OddsAPIClient): Initialized API client

    Returns:
        list: List of game events
    """
    print("Fetching today's NHL games...")
    events = client.get_events(sport='icehockey_nhl')

    if len(events) == 0:
        print("⚠️  No NHL games found for today")
        return []

    print(f"✓ Found {len(events)} NHL games\n")

    # Display games
    for i, event in enumerate(events, 1):
        print(f"  {i}. {event['away_team']} @ {event['home_team']} ({event['commence_time']})")

    return events


def pull_game_lines(client, game_id, bookmaker='fanduel'):
    """
    Pull SOG lines for a specific game.

    Args:
        client (OddsAPIClient): Initialized API client
        game_id (str): The Odds API event ID
        bookmaker (str): Bookmaker to pull from

    Returns:
        DataFrame: Player SOG lines (player_name, line, over_odds, under_odds)
        None if no props available
    """
    try:
        event_odds = client.get_event_odds(
            sport='icehockey_nhl',
            event_id=game_id,
            regions='us',
            markets='player_shots_on_goal',
            odds_format='american',
            bookmakers=bookmaker
        )

        bookmakers = event_odds.get('bookmakers', [])

        if len(bookmakers) == 0:
            return None

        # Extract props
        props = []
        for bm in bookmakers:
            for market in bm.get('markets', []):
                if market['key'] != 'player_shots_on_goal':
                    continue

                for outcome in market.get('outcomes', []):
                    props.append({
                        'player_name': outcome.get('description'),
                        'over_under': outcome.get('name'),
                        'line': outcome.get('point'),
                        'odds': outcome.get('price')
                    })

        if len(props) == 0:
            return None

        # Pivot to get Over/Under on same row
        props_df = pd.DataFrame(props)
        props_pivot = props_df.pivot_table(
            index=['player_name', 'line'],
            columns='over_under',
            values='odds',
            aggfunc='first'
        ).reset_index()

        props_pivot.columns.name = None
        if 'Over' in props_pivot.columns:
            props_pivot['over_odds'] = props_pivot['Over']
        if 'Under' in props_pivot.columns:
            props_pivot['under_odds'] = props_pivot['Under']

        props_pivot = props_pivot[['player_name', 'line', 'over_odds', 'under_odds']]

        return props_pivot

    except Exception as e:
        print(f"    ✗ Error pulling lines: {e}")
        return None


def get_nhl_game_id(game_date, away_team, home_team):
    """
    Get NHL game ID from schedule API.

    Args:
        game_date: Date in YYYY-MM-DD format
        away_team: Away team name
        home_team: Home team name

    Returns:
        NHL game ID or None if not found
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
        print(f"    Error fetching NHL game ID: {e}")
        return None


def run_predictions_for_game(game_lines, game_info, player_mapping, bookmaker='fanduel'):
    """
    Run model predictions for all players in a game.

    Args:
        game_lines (DataFrame): Player lines from pull_game_lines()
        game_info (dict): Game metadata (id, away_team, home_team, commence_time)
        player_mapping (dict): Player name -> ID mapping
        bookmaker (str): Bookmaker name

    Returns:
        list: List of prediction dictionaries
    """
    predictions = []

    # Get NHL game ID from schedule API
    import requests
    game_time = pd.to_datetime(game_info['commence_time'])

    # Convert to EST and get game date
    if game_time.tz is None:
        game_time_est = game_time.tz_localize('UTC').tz_convert('America/New_York')
    else:
        game_time_est = game_time.tz_convert('America/New_York')

    game_date = game_time_est.strftime('%Y-%m-%d')

    nhl_game_id = get_nhl_game_id(game_date, game_info['away_team'], game_info['home_team'])

    if nhl_game_id:
        print(f"    ✓ NHL game ID: {nhl_game_id}")
    else:
        print(f"    ⚠️  Could not find NHL game ID")

    # Load player data once for this game
    df_player = pd.read_csv('data/player_game_logs_2025_2026_with_opponent.csv')

    for idx, row in game_lines.iterrows():
        player_name = row['player_name']
        line = row['line']
        over_odds = row['over_odds']
        under_odds = row['under_odds']

        # Get player ID
        player_id = player_mapping.get(player_name)

        if player_id is None:
            continue

        try:
            # Get player team
            player_games = df_player[df_player['player_id'] == player_id]

            if len(player_games) == 0:
                continue

            player_team = player_games.iloc[0]['team_abbrev']

            # Determine home/away
            home_away = 'H' if player_team in game_info['home_team'] else 'A'

            # Make prediction
            prediction = predict_shots(player_id, home_away)

            if prediction is None:
                continue

            # Calculate metrics
            difference = prediction - line
            abs_diff = abs(difference)

            # Determine bet type and calculate Poisson probabilities
            if abs_diff < 0.2:
                # NO BET - too close to call
                recommendation = "NO BET"
                model_probability = None
                implied_probability = None
                true_edge = None
                confidence = "LOW"
            elif difference > 0:
                # OVER bet
                recommendation = f"BET OVER {line}"
                bet_type = 'OVER'
                relevant_odds = over_odds

                # Calculate true edge using Poisson
                model_probability = calculate_poisson_probability(prediction, line, bet_type)
                implied_probability = odds_to_implied_prob(relevant_odds)
                true_edge = (model_probability - implied_probability) * 100

                # Confidence based on true edge
                if true_edge > 10:
                    confidence = "HIGH"
                elif true_edge > 5:
                    confidence = "MEDIUM"
                else:
                    confidence = "LOW"
            else:
                # UNDER bet
                recommendation = f"BET UNDER {line}"
                bet_type = 'UNDER'
                relevant_odds = under_odds

                # Calculate true edge using Poisson
                model_probability = calculate_poisson_probability(prediction, line, bet_type)
                implied_probability = odds_to_implied_prob(relevant_odds)
                true_edge = (model_probability - implied_probability) * 100

                # Confidence based on true edge
                if true_edge > 10:
                    confidence = "HIGH"
                elif true_edge > 5:
                    confidence = "MEDIUM"
                else:
                    confidence = "LOW"

            # Store prediction
            predictions.append({
                'game_id': game_info['id'],
                'nhl_game_id': nhl_game_id,  # NHL game ID from schedule API
                'game_time': game_info['commence_time'],
                'away_team': game_info['away_team'],
                'home_team': game_info['home_team'],
                'prediction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'player_name': player_name,
                'player_id': player_id,
                'team': player_team,
                'home_away': home_away,
                'line': line,
                'over_odds': over_odds,
                'under_odds': under_odds,
                'prediction': prediction,
                'difference': difference,
                'confidence': confidence,
                'true_edge': true_edge,
                'model_probability': model_probability,
                'implied_probability': implied_probability,
                'recommendation': recommendation,
                'bookmaker': bookmaker,
                'actual_shots': None,
                'result': None
            })

        except Exception as e:
            continue

    return predictions


def save_predictions(predictions_df):
    """
    Save predictions to predictions_history_v2.csv with Poisson-based true edge.
    Deduplicates by game_id + player_id, keeping the most recent prediction.

    Args:
        predictions_df (DataFrame): Predictions to save
    """
    predictions_file = 'data/predictions_history_v2.csv'

    if os.path.exists(predictions_file):
        existing = pd.read_csv(predictions_file)
        combined = pd.concat([existing, predictions_df], ignore_index=True)

        # Deduplicate: keep most recent prediction for each game_id + player_id
        # Sort by prediction_date to ensure we keep the latest
        combined['prediction_date'] = pd.to_datetime(combined['prediction_date'])
        combined = combined.sort_values('prediction_date', ascending=True)

        # Drop duplicates, keeping the last (most recent) entry
        initial_count = len(combined)
        combined = combined.drop_duplicates(subset=['game_id', 'player_id'], keep='last')
        duplicates_removed = initial_count - len(combined)

        # Convert prediction_date back to string format
        combined['prediction_date'] = combined['prediction_date'].dt.strftime('%Y-%m-%d %H:%M:%S')

        combined.to_csv(predictions_file, index=False)

        if duplicates_removed > 0:
            print(f"✓ Appended {len(predictions_df)} predictions, removed {duplicates_removed} duplicates")
        else:
            print(f"✓ Appended {len(predictions_df)} predictions (no duplicates found)")
        print(f"  Total predictions in file: {len(combined)}")
    else:
        predictions_df.to_csv(predictions_file, index=False)
        print(f"✓ Created {predictions_file} with {len(predictions_df)} predictions")


def print_summary(predictions_df, games_found, games_with_props):
    """
    Print analysis summary.

    Args:
        predictions_df (DataFrame): All predictions
        games_found (int): Number of games found
        games_with_props (int): Number of games with props
    """
    print("\n" + "="*80)
    print("ANALYSIS SUMMARY")
    print("="*80)
    print(f"\nGames found: {games_found}")
    print(f"Games with props: {games_with_props}")
    print(f"Total predictions: {len(predictions_df)}")

    # Confidence breakdown
    high_conf = (predictions_df['confidence'] == 'HIGH').sum()
    med_conf = (predictions_df['confidence'] == 'MEDIUM').sum()
    low_conf = (predictions_df['confidence'] == 'LOW').sum()

    print(f"\nConfidence breakdown:")
    print(f"  HIGH:   {high_conf} ({high_conf/len(predictions_df)*100:.1f}%)")
    print(f"  MEDIUM: {med_conf} ({med_conf/len(predictions_df)*100:.1f}%)")
    print(f"  LOW:    {low_conf} ({low_conf/len(predictions_df)*100:.1f}%)")

    # Show high confidence bets (true_edge > 10%)
    high_conf_bets = predictions_df[predictions_df['confidence'] == 'HIGH']

    if len(high_conf_bets) > 0:
        print(f"\n{'='*80}")
        print("HIGH CONFIDENCE BETS (True Edge > 10%)")
        print("="*80)
        print(high_conf_bets[['player_name', 'line', 'prediction', 'true_edge', 'recommendation']].to_string(index=False))
    else:
        print("\n⚠️  No high confidence bets found today")


def update_player_data():
    """
    Update player game logs with latest data from NHL API.
    This includes:
    1. Fetching latest player game logs for 2025-2026 season
    2. Adding engineered features
    3. Updating team game stats (incremental)
    4. Adding opponent features

    Returns:
        bool: True if successful, False otherwise
    """
    print("\n" + "="*80)
    print("UPDATING PLAYER DATA WITH LATEST GAMES")
    print("="*80)

    try:
        with NHLAPIClient() as client:
            # Step 1: Fetch last night's games (incremental update)
            print("\nStep 1: Fetching last night's games from NHL API")
            print("-"*80)

            # Calculate yesterday's date
            from datetime import timedelta
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            print(f"Fetching games from: {yesterday}")

            client.update_player_game_logs_incremental(
                date=yesterday,
                season_id="20252026",
                game_type=2,
                csv_file="data/player_game_logs_2025_2026.csv"
            )

            # Step 2: Add engineered features (overwrites the same file)
            print("\nStep 2: Adding engineered features")
            print("-"*80)

            NHLAPIClient.add_engineered_features(
                input_file="data/player_game_logs_2025_2026.csv",
                output_file="data/player_game_logs_2025_2026.csv"
            )

            # Step 3: Update team game stats (incremental - only fetches new games)
            print("\nStep 3: Updating team game stats")
            print("-"*80)
            print("(Using incremental update - only fetching new games)")

            client.build_team_game_stats_from_csvs(
                input_files=[
                    'data/player_game_logs_2023_2024.csv',
                    'data/player_game_logs_2024_2025.csv',
                    'data/player_game_logs_2025_2026.csv'
                ],
                output_file='data/team_game_stats.csv'
            )

            # Step 4: Add opponent features
            print("\nStep 4: Adding opponent defensive features")
            print("-"*80)

            add_opponent_features(
                input_file='data/player_game_logs_2025_2026.csv',
                output_file='data/player_game_logs_2025_2026_with_opponent.csv',
                team_stats_file='data/team_game_stats.csv'
            )

        print("\n" + "="*80)
        print("DATA UPDATE COMPLETE!")
        print("="*80)
        print("✓ Player data is now up to date with last night's games\n")

        return True

    except Exception as e:
        print(f"\n✗ ERROR updating player data: {e}")
        import traceback
        traceback.print_exc()
        print("\n⚠️  Continuing with existing data...\n")
        return False


def run_daily_analysis(api_key='2b7aa5b8da44c20602b4aa972245c181', bookmaker='fanduel', update_data=True):
    """
    Main function to run daily NHL betting analysis.

    This orchestrates the entire workflow:
    0. Update player data with last night's games (if update_data=True)
    1. Get today's games
    2. Pull lines for each game
    3. Run predictions with updated data
    4. Save results

    Args:
        api_key (str): The Odds API key
        bookmaker (str): Bookmaker to pull lines from (default: fanduel)
        update_data (bool): Whether to update player data first (default: True)

    Returns:
        DataFrame: All predictions made
    """
    print("="*80)
    print("AUTOMATED DAILY NHL BETTING ANALYSIS")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Bookmaker: {bookmaker}\n")

    # Step 0: Update player data with latest games
    if update_data:
        print("="*80)
        print("PHASE 1: DATA UPDATE")
        print("="*80)
        update_player_data()

    print("="*80)
    print("PHASE 2: PREDICTION GENERATION")
    print("="*80)

    client = OddsAPIClient(api_key)
    all_predictions = []

    try:
        # Step 1: Get today's games
        print("\nStep 1: Getting today's games")
        print("-"*80)
        events = get_todays_games(client)

        if len(events) == 0:
            return pd.DataFrame()

        # Step 2: Load player mapping and model
        print("\nStep 2: Loading player mapping and model")
        print("-"*80)
        player_mapping = load_player_mapping()
        model, feature_cols = get_model()

        # Step 3: Process each game
        print("\nStep 3: Processing each game")
        print("-"*80)

        games_with_props = 0

        for game_num, event in enumerate(events, 1):
            game_info = {
                'id': event['id'],
                'away_team': event['away_team'],
                'home_team': event['home_team'],
                'commence_time': event['commence_time']
            }

            print(f"\n  Game {game_num}/{len(events)}: {game_info['away_team']} @ {game_info['home_team']}")

            # Rate limiting
            if game_num > 1:
                time.sleep(0.5)

            # Pull lines
            game_lines = pull_game_lines(client, game_info['id'], bookmaker)

            if game_lines is None:
                print(f"    ⚠️  No props available yet - SKIPPING")
                continue

            print(f"    ✓ Found {len(game_lines)} players with lines")
            games_with_props += 1

            # Run predictions
            game_predictions = run_predictions_for_game(
                game_lines,
                game_info,
                player_mapping,
                bookmaker
            )

            print(f"    ✓ Generated {len(game_predictions)} predictions")
            all_predictions.extend(game_predictions)

        # Step 4: Save predictions
        print("\nStep 4: Saving predictions")
        print("-"*80)

        if len(all_predictions) == 0:
            print("⚠️  No predictions generated (props may not be available yet)")
            print("Try running again closer to game time (1-2 hours before)")
            return pd.DataFrame()

        predictions_df = pd.DataFrame(all_predictions)
        save_predictions(predictions_df)

        # Step 5: Print summary
        print_summary(predictions_df, len(events), games_with_props)

        print("\n" + "="*80)
        print("ANALYSIS COMPLETE!")
        print("="*80)
        print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return predictions_df

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

    finally:
        client.close()


if __name__ == "__main__":
    # Run the daily analysis
    predictions = run_daily_analysis()

    # Exit with appropriate code for cron job monitoring
    if len(predictions) > 0:
        exit(0)  # Success
    else:
        exit(1)  # No predictions generated