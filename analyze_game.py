import pandas as pd
from datetime import datetime
from odds_api import OddsAPIClient
from simple_predict import predict_shots, get_model
import os


def get_player_id_mapping():
    """
    Create a mapping from player names to player IDs.
    Uses the current season data to build the mapping.
    """
    print("Loading player ID mapping...")

    df = pd.read_csv('data/player_game_logs_2025_2026_with_opponent.csv')

    # Get unique players - need to infer player names from the data
    # Since we don't have player names in our data, we'll need to create a lookup
    # For now, we'll load what we have and the user can provide a mapping file

    # Check if a manual mapping file exists
    mapping_file = 'data/player_name_to_id.csv'

    if os.path.exists(mapping_file):
        mapping_df = pd.read_csv(mapping_file)
        mapping = dict(zip(mapping_df['player_name'], mapping_df['player_id']))
        print(f"✓ Loaded {len(mapping)} player mappings from {mapping_file}")
        return mapping
    else:
        print(f"⚠️  No player mapping file found at {mapping_file}")
        print("Creating empty mapping - you'll need to add player name->ID mappings")
        return {}


def analyze_game_lines(game_id, api_key, bookmaker='fanduel', save_predictions=True):
    """
    Analyze all SOG lines for a specific game.

    Args:
        game_id (str): The Odds API event ID
        api_key (str): The Odds API key
        bookmaker (str): Which bookmaker to use (default: fanduel)
        save_predictions (bool): Whether to save predictions to tracking file

    Returns:
        DataFrame: Analysis results with predictions and recommendations
    """
    print("="*80)
    print("NHL SHOTS-ON-GOAL LINE ANALYZER")
    print("="*80)
    print(f"Game ID: {game_id}")
    print(f"Bookmaker: {bookmaker}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Initialize API client
    client = OddsAPIClient(api_key)

    try:
        # Step 1: Fetch game lines
        print("Step 1: Fetching SOG lines...")
        print("-"*80)

        event_odds = client.get_event_odds(
            sport='icehockey_nhl',
            event_id=game_id,
            regions='us',
            markets='player_shots_on_goal',
            odds_format='american',
            bookmakers=bookmaker
        )

        away_team = event_odds['away_team']
        home_team = event_odds['home_team']
        game_time = event_odds['commence_time']

        print(f"\n✓ Game: {away_team} @ {home_team}")
        print(f"  Start: {game_time}")

        bookmakers = event_odds.get('bookmakers', [])

        if len(bookmakers) == 0:
            print(f"\n✗ No {bookmaker} lines available for this game yet.")
            client.close()
            return pd.DataFrame()

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

        print(f"\n✓ Found {len(props_pivot)} players with SOG lines")

        # Step 2: Load player ID mapping
        print("\nStep 2: Loading player ID mapping...")
        print("-"*80)

        player_mapping = get_player_id_mapping()

        # Step 3: Load model
        print("\nStep 3: Loading prediction model...")
        print("-"*80)

        model, feature_cols = get_model()

        # Step 4: Run predictions for each player
        print("\nStep 4: Running predictions...")
        print("-"*80)

        results = []

        for idx, row in props_pivot.iterrows():
            player_name = row['player_name']
            line = row['line']
            over_odds = row['over_odds']
            under_odds = row['under_odds']

            # Determine if player is home or away
            # This is a simplification - in reality you'd need to check team rosters
            # For now, we'll need to infer or require this info

            # Try to get player ID from mapping
            player_id = player_mapping.get(player_name)

            if player_id is None:
                print(f"  ⚠️  {player_name}: No player ID mapping found - SKIPPED")
                results.append({
                    'player_name': player_name,
                    'player_id': None,
                    'team': 'Unknown',
                    'home_away': 'Unknown',
                    'line': line,
                    'over_odds': over_odds,
                    'under_odds': under_odds,
                    'prediction': None,
                    'difference': None,
                    'confidence': 'N/A',
                    'recommendation': 'NO PLAYER ID',
                    'edge': None
                })
                continue

            # Determine home/away (you'll need team roster info for this)
            # For now, we'll make an educated guess based on player data
            try:
                df_player = pd.read_csv('data/player_game_logs_2025_2026_with_opponent.csv')
                player_games = df_player[df_player['player_id'] == player_id]

                if len(player_games) == 0:
                    print(f"  ⚠️  {player_name}: Player not found in database - SKIPPED")
                    results.append({
                        'player_name': player_name,
                        'player_id': player_id,
                        'team': 'Unknown',
                        'home_away': 'Unknown',
                        'line': line,
                        'over_odds': over_odds,
                        'under_odds': under_odds,
                        'prediction': None,
                        'difference': None,
                        'confidence': 'N/A',
                        'recommendation': 'NOT IN DATABASE',
                        'edge': None
                    })
                    continue

                # Get player's team
                player_team = player_games.iloc[0]['team_abbrev']

                # Determine home/away
                # This requires mapping full team names to abbreviations
                # For now, we'll assume this needs to be done manually
                home_away = 'H' if player_team in home_team else 'A'

                # Make prediction
                prediction = predict_shots(player_id, home_away)

                if prediction is None:
                    print(f"  ⚠️  {player_name}: Prediction failed - SKIPPED")
                    results.append({
                        'player_name': player_name,
                        'player_id': player_id,
                        'team': player_team,
                        'home_away': home_away,
                        'line': line,
                        'over_odds': over_odds,
                        'under_odds': under_odds,
                        'prediction': None,
                        'difference': None,
                        'confidence': 'N/A',
                        'recommendation': 'PREDICTION FAILED',
                        'edge': None
                    })
                    continue

                # Calculate difference from line
                difference = prediction - line

                # Determine confidence
                abs_diff = abs(difference)
                if abs_diff > 0.5:
                    confidence = "HIGH"
                elif abs_diff > 0.25:
                    confidence = "MEDIUM"
                else:
                    confidence = "LOW"

                # Make recommendation
                if abs_diff < 0.2:
                    recommendation = "NO BET"
                    edge = None
                elif difference > 0:
                    recommendation = f"BET OVER {line}"
                    # Calculate edge
                    edge = (difference / line) * 100
                else:
                    recommendation = f"BET UNDER {line}"
                    edge = (abs(difference) / line) * 100

                print(f"  ✓ {player_name}: Pred={prediction:.2f}, Line={line}, Diff={difference:+.2f}, {recommendation}")

                results.append({
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
                    'recommendation': recommendation,
                    'edge': edge
                })

            except Exception as e:
                print(f"  ✗ {player_name}: Error - {e}")
                results.append({
                    'player_name': player_name,
                    'player_id': player_mapping.get(player_name),
                    'team': 'Unknown',
                    'home_away': 'Unknown',
                    'line': line,
                    'over_odds': over_odds,
                    'under_odds': under_odds,
                    'prediction': None,
                    'difference': None,
                    'confidence': 'N/A',
                    'recommendation': f'ERROR: {str(e)[:50]}',
                    'edge': None
                })

        # Create results DataFrame
        results_df = pd.DataFrame(results)

        # Add metadata
        results_df['game_id'] = game_id
        results_df['away_team'] = away_team
        results_df['home_team'] = home_team
        results_df['game_time'] = game_time
        results_df['prediction_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        results_df['bookmaker'] = bookmaker
        results_df['actual_shots'] = None  # To be filled in later
        results_df['result'] = None  # To be filled in later (Win/Loss/Push)

        # Reorder columns
        results_df = results_df[[
            'game_id', 'game_time', 'away_team', 'home_team',
            'prediction_date', 'player_name', 'player_id', 'team', 'home_away',
            'line', 'over_odds', 'under_odds', 'prediction', 'difference',
            'confidence', 'edge', 'recommendation', 'bookmaker',
            'actual_shots', 'result'
        ]]

        # Save predictions
        if save_predictions:
            print("\nStep 5: Saving predictions...")
            print("-"*80)

            predictions_file = 'data/predictions_history.csv'

            if os.path.exists(predictions_file):
                # Append to existing file
                existing = pd.read_csv(predictions_file)
                combined = pd.concat([existing, results_df], ignore_index=True)
                combined.to_csv(predictions_file, index=False)
                print(f"✓ Appended {len(results_df)} predictions to {predictions_file}")
            else:
                # Create new file
                results_df.to_csv(predictions_file, index=False)
                print(f"✓ Created {predictions_file} with {len(results_df)} predictions")

        # Display summary
        print("\n" + "="*80)
        print("ANALYSIS SUMMARY")
        print("="*80)

        # Filter to valid predictions only
        valid_preds = results_df[results_df['prediction'].notna()]

        if len(valid_preds) == 0:
            print("\n⚠️  No valid predictions could be made.")
            print("   Make sure player name->ID mapping file exists.")
        else:
            print(f"\nTotal players: {len(results_df)}")
            print(f"Valid predictions: {len(valid_preds)}")
            print(f"High confidence: {(valid_preds['confidence'] == 'HIGH').sum()}")
            print(f"Medium confidence: {(valid_preds['confidence'] == 'MEDIUM').sum()}")
            print(f"Low confidence: {(valid_preds['confidence'] == 'LOW').sum()}")

            # Show recommendations
            bets = valid_preds[valid_preds['recommendation'].str.contains('BET', na=False)]

            if len(bets) > 0:
                print(f"\n{'='*80}")
                print("RECOMMENDED BETS")
                print("="*80)
                print(f"\n{bets[['player_name', 'line', 'prediction', 'confidence', 'edge', 'recommendation']].to_string(index=False)}")
            else:
                print("\n⚠️  No betting opportunities found with current confidence thresholds")

        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)

        return results_df

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()
    finally:
        client.close()


if __name__ == "__main__":
    import sys

    API_KEY = '2b7aa5b8da44c20602b4aa972245c181'

    if len(sys.argv) > 1:
        game_id = sys.argv[1]
    else:
        # Example game ID
        game_id = '17233f3e18774f0a1544acb5e924ed87'
        print(f"No game ID provided, using example: {game_id}\n")

    # Run analysis
    results = analyze_game_lines(game_id, API_KEY, bookmaker='fanduel')

    if len(results) > 0:
        print(f"\nResults saved to: data/predictions_history.csv")
        print("\nTo analyze another game:")
        print(f"  python3 analyze_game.py <game_id>")