import pandas as pd
import lightgbm as lgb
import joblib
import os


# Global variables to cache model
_MODEL = None
_FEATURE_COLS = None

# Model file paths
MODEL_FILE = 'models/shots_model.pkl'
FEATURES_FILE = 'models/feature_cols.pkl'


def odds_to_probability(odds_str):
    """Convert American odds to implied probability."""
    odds = int(odds_str)
    if odds > 0:
        # Positive odds (e.g., +120)
        return 100 / (odds + 100)
    else:
        # Negative odds (e.g., -154)
        return abs(odds) / (abs(odds) + 100)


def odds_to_payout(odds_str, bet_amount=100):
    """Calculate payout for a winning bet."""
    odds = int(odds_str)
    if odds > 0:
        # Positive odds
        return bet_amount * (odds / 100)
    else:
        # Negative odds
        return bet_amount * (100 / abs(odds))


def get_model():
    """Load or train the model (cached for efficiency)."""
    global _MODEL, _FEATURE_COLS

    # Check in-memory cache first
    if _MODEL is not None:
        return _MODEL, _FEATURE_COLS

    # Try to load from disk
    if os.path.exists(MODEL_FILE) and os.path.exists(FEATURES_FILE):
        print("Loading saved model...")
        _MODEL = joblib.load(MODEL_FILE)
        _FEATURE_COLS = joblib.load(FEATURES_FILE)
        print("✓ Model loaded\n")
        return _MODEL, _FEATURE_COLS

    # Train new model if not found
    print("Training model (one-time setup)...")

    # Load training data
    season_2023_2024 = pd.read_csv('data/player_game_logs_2023_2024_with_opponent.csv')
    season_2024_2025 = pd.read_csv('data/player_game_logs_2024_2025_with_opponent.csv')
    train_df = pd.concat([season_2023_2024, season_2024_2025], ignore_index=True)

    # Define features
    exclude_cols = [
        'player_id', 'game_id', 'season_id', 'game_type', 'game_date',
        'team_abbrev', 'opponent_abbrev', 'position_code',
        'shots', 'goals', 'assists', 'points', 'plus_minus',
        'power_play_goals', 'power_play_points',
        'shorthanded_goals', 'shorthanded_points',
        'pim', 'shifts', 'toi_raw', 'toi_minutes'
    ]

    _FEATURE_COLS = [col for col in train_df.columns if col not in exclude_cols]

    X_train = train_df[_FEATURE_COLS]
    y_train = train_df['shots']

    # Remove NaN
    train_mask = ~(X_train.isna().any(axis=1) | y_train.isna())
    X_train = X_train[train_mask]
    y_train = y_train[train_mask]

    # Train model
    _MODEL = lgb.LGBMRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        num_leaves=15,
        min_child_samples=20,
        random_state=42,
        n_jobs=-1,
        verbose=-1
    )

    _MODEL.fit(X_train, y_train)

    # Save model to disk
    os.makedirs('models', exist_ok=True)
    joblib.dump(_MODEL, MODEL_FILE)
    joblib.dump(_FEATURE_COLS, FEATURES_FILE)
    print("✓ Model trained and saved\n")

    return _MODEL, _FEATURE_COLS


def predict_shots(player_id, home_away='H'):
    """
    Predict shots for a player's next game.

    Args:
        player_id (int): NHL player ID
        home_away (str): 'H' for home, 'A' for away

    Returns:
        float: Predicted shots for the game
    """
    # Get model
    model, feature_cols = get_model()

    # Load current season data
    df = pd.read_csv('data/player_game_logs_2025_2026_with_opponent.csv')

    # Find player
    player_games = df[df['player_id'] == player_id].copy()

    if len(player_games) == 0:
        print(f"ERROR: Player {player_id} not found in database")
        return None

    # Get most recent game stats
    player_games['game_date'] = pd.to_datetime(player_games['game_date'])
    player_games = player_games.sort_values('game_date', ascending=False)
    recent_game = player_games.iloc[0]

    # Create feature vector for next game
    features = {}
    for col in feature_cols:
        if col in recent_game.index:
            features[col] = recent_game[col]

    # Set home/away flag
    features['home_flag'] = 1 if home_away.upper() == 'H' else 0

    # Assume 2 days since last game (typical)
    features['days_since_last_game'] = 2

    # Create DataFrame
    feature_df = pd.DataFrame([features])[feature_cols]

    # Make prediction
    prediction = model.predict(feature_df)[0]

    return prediction


def predict_and_display(player_id, home_away='H', line=None, over_odds=None, under_odds=None):
    """
    Predict and display results with context.

    Args:
        player_id (int): NHL player ID
        home_away (str): 'H' for home, 'A' for away
        line (float, optional): Betting line to compare against
        over_odds (str, optional): Odds for over (e.g., '-154', '+120')
        under_odds (str, optional): Odds for under (e.g., '+120', '-154')
    """
    # Get player info
    df = pd.read_csv('data/player_game_logs_2025_2026_with_opponent.csv')
    player_games = df[df['player_id'] == player_id].copy()

    if len(player_games) == 0:
        print(f"ERROR: Player {player_id} not found")
        return

    # Get most recent stats
    player_games['game_date'] = pd.to_datetime(player_games['game_date'])
    player_games = player_games.sort_values('game_date', ascending=False)
    recent = player_games.iloc[0]

    # Calculate stats
    season_avg = recent['shots_season_to_date'] / recent['games_played_so_far']
    last10_avg = recent['shots_last10_avg']
    last5_avg = recent['shots_last5_avg']

    # Make prediction
    prediction = predict_shots(player_id, home_away)

    # Display
    print("="*60)
    print(f"PREDICTION FOR PLAYER {player_id}")
    print("="*60)

    print(f"\nLocation: {'HOME' if home_away.upper() == 'H' else 'AWAY'}")

    print(f"\nPlayer Statistics:")
    print(f"  Season average:    {season_avg:.2f} shots/game")
    print(f"  Last 10 games:     {last10_avg:.2f} shots/game")
    print(f"  Last 5 games:      {last5_avg:.2f} shots/game")
    print(f"  Most recent game:  {recent['shots_last1']:.0f} shots")

    print(f"\n{'='*60}")
    print(f"MODEL PREDICTION: {prediction:.2f} shots")
    print(f"{'='*60}")

    if line is not None:
        print(f"\n{'='*60}")
        print(f"BETTING ANALYSIS")
        print(f"{'='*60}")

        print(f"\nLine: {line} shots")

        # Display odds if provided
        if over_odds and under_odds:
            over_prob = odds_to_probability(over_odds)
            under_prob = odds_to_probability(under_odds)
            over_payout = odds_to_payout(over_odds, 100)
            under_payout = odds_to_payout(under_odds, 100)

            print(f"\nOdds:")
            print(f"  Over {line}:  {over_odds} (Implied: {over_prob*100:.1f}%, Payout: ${over_payout:.2f} on $100)")
            print(f"  Under {line}: {under_odds} (Implied: {under_prob*100:.1f}%, Payout: ${under_payout:.2f} on $100)")

        distance = prediction - line

        print(f"\nModel Analysis:")
        if abs(distance) < 0.2:
            print(f"  ⚠️  TOO CLOSE ({distance:+.2f} from line)")
            print(f"\n  ❌ RECOMMENDATION: NO BET (too uncertain)")
        elif distance > 0:
            print(f"  📈 Model leans OVER {line} ({distance:+.2f} above line)")
            if last10_avg > line:
                print(f"  ✓ Last 10 avg ({last10_avg:.2f}) supports OVER")
            else:
                print(f"  ⚠️  Last 10 avg ({last10_avg:.2f}) does NOT support")

            # Confidence
            confidence = abs(distance)
            if confidence > 0.5:
                conf_level = "MEDIUM-HIGH"
                emoji = "✅"
            elif confidence > 0.25:
                conf_level = "LOW-MEDIUM"
                emoji = "⚠️"
            else:
                conf_level = "LOW"
                emoji = "🔴"

            print(f"  {emoji} Confidence: {conf_level} ({confidence:.2f} shots from line)")

            # Final recommendation
            if over_odds:
                print(f"\n  {'✅' if confidence > 0.3 else '⚠️'} RECOMMENDATION: {'BET' if confidence > 0.3 else 'CONSIDER'} OVER {line} at {over_odds}")
            else:
                print(f"\n  RECOMMENDATION: Bet OVER {line}")
        else:
            print(f"  📉 Model leans UNDER {line} ({abs(distance):.2f} below line)")
            if last10_avg < line:
                print(f"  ✓ Last 10 avg ({last10_avg:.2f}) supports UNDER")
            else:
                print(f"  ⚠️  Last 10 avg ({last10_avg:.2f}) does NOT support")

            # Confidence
            confidence = abs(distance)
            if confidence > 0.5:
                conf_level = "MEDIUM-HIGH"
                emoji = "✅"
            elif confidence > 0.25:
                conf_level = "LOW-MEDIUM"
                emoji = "⚠️"
            else:
                conf_level = "LOW"
                emoji = "🔴"

            print(f"  {emoji} Confidence: {conf_level} ({confidence:.2f} shots from line)")

            # Final recommendation
            if under_odds:
                print(f"\n  {'✅' if confidence > 0.3 else '⚠️'} RECOMMENDATION: {'BET' if confidence > 0.3 else 'CONSIDER'} UNDER {line} at {under_odds}")
            else:
                print(f"\n  RECOMMENDATION: Bet UNDER {line}")

    print(f"\n⚠️  Model uncertainty: ±1.05 shots (68% confidence interval)")
    if line:
        print(f"    Prediction range: {prediction-1.05:.2f} to {prediction+1.05:.2f}")

    return prediction


# Example usage
if __name__ == "__main__":
    print("SIMPLE PREDICTION FUNCTION\n")

    # Example 1: Just get the prediction
    print("Example 1: Quick prediction")
    print("-" * 60)
    prediction = predict_shots(8476887, 'H')  # Filip Forsberg, home
    print(f"Filip Forsberg (Home): {prediction:.2f} shots\n")

    # Example 2: Full analysis with line and odds
    print("\nExample 2: Full analysis with betting line and odds")
    print("-" * 60)
    predict_and_display(8476887, 'H', line=2.5, over_odds='-154', under_odds='+120')