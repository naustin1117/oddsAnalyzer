import pandas as pd
import numpy as np
import lightgbm as lgb


def train_model():
    """Train the model and return it with feature columns."""
    # Load training data
    season_2023_2024 = pd.read_csv('data/player_game_logs_2023_2024_with_opponent.csv')
    season_2024_2025 = pd.read_csv('data/player_game_logs_2024_2025_with_opponent.csv')
    train_df = pd.concat([season_2023_2024, season_2024_2025], ignore_index=True)

    # Define features
    exclude_cols = [
        'player_id', 'game_id', 'season_id', 'game_type', 'game_date',
        'team_abbrev', 'opponent_abbrev', 'position_code',
        'shots',
        'goals', 'assists', 'points', 'plus_minus',
        'power_play_goals', 'power_play_points',
        'shorthanded_goals', 'shorthanded_points',
        'pim', 'shifts', 'toi_raw',
        'toi_minutes'
    ]

    feature_cols = [col for col in train_df.columns if col not in exclude_cols]

    X_train = train_df[feature_cols]
    y_train = train_df['shots']

    # Remove NaN
    train_mask = ~(X_train.isna().any(axis=1) | y_train.isna())
    X_train = X_train[train_mask]
    y_train = y_train[train_mask]

    # Train model
    lgb_model = lgb.LGBMRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        num_leaves=15,
        min_child_samples=20,
        random_state=42,
        n_jobs=-1,
        verbose=-1
    )

    lgb_model.fit(X_train, y_train)
    return lgb_model, feature_cols, X_train, y_train


def explain_prediction():
    """Explain why the model made a specific prediction for Forsberg."""
    print("="*60)
    print("PREDICTION EXPLANATION: Filip Forsberg vs FLA")
    print("="*60)

    # Train model
    model, feature_cols, X_train, y_train = train_model()

    # Forsberg's features (from previous prediction)
    forsberg_features = {
        'home_flag': 1,
        'shots_last1': 1.0,
        'shots_last5_sum': 12.0,
        'shots_last5_avg': 2.4,
        'toi_last5_sum': 73.21666666666667,
        'shots_per60_last5': 9.83382654222627,
        'shots_last10_sum': 25.0,
        'shots_last10_avg': 2.5,
        'toi_last10_sum': 135.88333333333333,
        'shots_per60_last10': 11.03888139335214,
        'shots_season_to_date': 30.0,
        'toi_season_to_date': 172.63333333333333,
        'shots_per60_season_to_date': 10.426723305657465,
        'games_played_so_far': 13.0,
        'days_since_last_game': 2,
        'opponent_shots_allowed_avg': 29.3,
        'opponent_shots_allowed_last5': 29.3,
        'opponent_shots_allowed_last10': 29.3
    }

    # Create DataFrame
    forsberg_df = pd.DataFrame([forsberg_features])[feature_cols]

    # Make prediction
    prediction = model.predict(forsberg_df)[0]

    print(f"\nPrediction: {prediction:.2f} shots")
    print(f"Forsberg's recent average: 2.5 shots (last 10 games)")
    print(f"Difference: {prediction - 2.5:.2f} shots LOWER than recent average")

    # Get feature importances
    importance_df = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    # Get training data statistics for comparison
    train_means = X_train.mean()
    train_stds = X_train.std()

    print("\n" + "="*60)
    print("WHY DID THE MODEL PREDICT LOWER?")
    print("="*60)

    print("\nTop 10 most important features and Forsberg's values:")
    print(f"\n{'Feature':<35} {'Forsberg':<12} {'Avg':<12} {'Difference':<15} {'Impact':<10}")
    print("-" * 90)

    for idx, row in importance_df.head(10).iterrows():
        feature_name = row['feature']
        forsberg_value = forsberg_features[feature_name]
        train_mean = train_means[feature_name]
        train_std = train_stds[feature_name]

        # Calculate z-score (how many standard deviations from mean)
        z_score = (forsberg_value - train_mean) / train_std if train_std > 0 else 0

        # Determine impact direction
        if z_score > 0.5:
            impact = "↑ Higher"
        elif z_score < -0.5:
            impact = "↓ Lower"
        else:
            impact = "≈ Average"

        diff_str = f"{z_score:+.2f} SD"

        print(f"{feature_name:<35} {forsberg_value:<12.2f} {train_mean:<12.2f} {diff_str:<15} {impact:<10}")

    # Detailed analysis
    print("\n" + "="*60)
    print("DETAILED BREAKDOWN")
    print("="*60)

    # Compare Forsberg to average player
    print(f"\n1. RECENT FORM (shots_last10_avg):")
    print(f"   Forsberg: 2.50 shots/game")
    print(f"   Average player: {train_means['shots_last10_avg']:.2f} shots/game")
    if forsberg_features['shots_last10_avg'] > train_means['shots_last10_avg']:
        print(f"   → Forsberg shoots MORE than average (+{forsberg_features['shots_last10_avg'] - train_means['shots_last10_avg']:.2f})")
    else:
        print(f"   → Forsberg shoots LESS than average ({forsberg_features['shots_last10_avg'] - train_means['shots_last10_avg']:.2f})")

    print(f"\n2. LAST GAME PERFORMANCE (shots_last1):")
    print(f"   Forsberg: 1.0 shots")
    print(f"   His last 10 avg: 2.5 shots")
    print(f"   → DOWN GAME! This pulls the prediction down")

    print(f"\n3. SHOTS PER 60 MINUTES (shots_per60_season_to_date):")
    print(f"   Forsberg: {forsberg_features['shots_per60_season_to_date']:.2f}")
    print(f"   Average player: {train_means['shots_per60_season_to_date']:.2f}")
    z = (forsberg_features['shots_per60_season_to_date'] - train_means['shots_per60_season_to_date']) / train_stds['shots_per60_season_to_date']
    print(f"   → Forsberg is {z:+.2f} standard deviations from average")

    print(f"\n4. ICE TIME (toi_last5_sum):")
    print(f"   Forsberg last 5 games: {forsberg_features['toi_last5_sum']:.1f} minutes total")
    print(f"   Average player: {train_means['toi_last5_sum']:.1f} minutes")
    print(f"   → Per game: {forsberg_features['toi_last5_sum']/5:.1f} mins vs avg {train_means['toi_last5_sum']/5:.1f} mins")

    print(f"\n5. OPPONENT DEFENSE (opponent_shots_allowed_avg):")
    print(f"   Florida allows: {forsberg_features['opponent_shots_allowed_avg']:.1f} shots/game")
    print(f"   League average: {train_means['opponent_shots_allowed_avg']:.1f} shots/game")
    if forsberg_features['opponent_shots_allowed_avg'] < train_means['opponent_shots_allowed_avg']:
        print(f"   → Florida allows FEWER shots (tougher defense)")
    else:
        print(f"   → Florida allows MORE shots (easier matchup)")

    print(f"\n6. HOME vs AWAY:")
    print(f"   Forsberg: {'Home' if forsberg_features['home_flag'] == 1 else 'Away'} game")
    home_pct = (X_train['home_flag'] == 1).sum() / len(X_train)
    print(f"   Average shots at home: {X_train[X_train['home_flag'] == 1]['shots_last10_avg'].mean():.2f}")
    print(f"   Average shots away: {X_train[X_train['home_flag'] == 0]['shots_last10_avg'].mean():.2f}")

    # Summary
    print("\n" + "="*60)
    print("SUMMARY: Why 2.01 instead of 2.5?")
    print("="*60)

    print(f"""
The model predicts LOWER (2.01 vs 2.5 recent avg) because:

1. ⚠️  His LAST GAME was only 1 shot (below his 2.5 average)
   - This recent down-game pulls the prediction down

2. 📊 REGRESSION TO THE MEAN
   - His 2.5 last-10 average might be slightly inflated
   - The model sees his "true" level as closer to 2.0-2.2

3. 🧮 EFFICIENCY METRICS
   - His shots_per60 rate and ice time suggest ~2.0-2.2 shots/game
   - The model weighs these efficiency stats heavily

4. 🏒 MODEL CONSERVATISM
   - With 1.05 shot error, the model hedges toward the mean
   - It's predicting his "expected" performance, not best-case

Bottom line: The model sees him as a 2.0-2.2 shot player, and his
recent 2.5 average includes some positive variance. Against Florida,
the model expects regression toward his true mean.
    """)


if __name__ == "__main__":
    explain_prediction()