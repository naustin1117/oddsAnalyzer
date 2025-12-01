import pandas as pd
import numpy as np
import lightgbm as lgb


def train_model():
    """Train the model on historical data."""
    print("Training model on historical data...")

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
    return lgb_model, feature_cols


def test_line_accuracy(line=2.5):
    """Test model accuracy on a specific line."""
    print("\n" + "="*60)
    print(f"TESTING MODEL ACCURACY ON {line} SHOT LINE")
    print("="*60)

    # Train model
    model, feature_cols = train_model()

    # Load test data (2025-2026 season)
    test_df = pd.read_csv('data/player_game_logs_2025_2026_with_opponent.csv')

    X_test = test_df[feature_cols]
    y_test = test_df['shots']

    # Remove NaN
    test_mask = ~(X_test.isna().any(axis=1) | y_test.isna())
    X_test = X_test[test_mask]
    y_test = y_test[test_mask]

    print(f"\nTotal test games: {len(y_test)}")

    # Make predictions
    predictions = model.predict(X_test)

    # Filter to games where line would likely be offered
    # (Players averaging between 1.5 and 4.5 shots per game)
    avg_shots = X_test['shots_last10_avg'].values
    relevant_mask = (avg_shots >= 1.0) & (avg_shots <= 4.0)

    y_relevant = y_test[relevant_mask]
    pred_relevant = predictions[relevant_mask]

    print(f"Games where {line} line would be offered: {len(y_relevant)}")

    # Actual results
    actual_over = (y_relevant > line).sum()
    actual_under = (y_relevant < line).sum()
    actual_push = (y_relevant == line).sum()

    print(f"\nActual results:")
    print(f"  Over {line}:  {actual_over} ({actual_over/len(y_relevant)*100:.1f}%)")
    print(f"  Under {line}: {actual_under} ({actual_under/len(y_relevant)*100:.1f}%)")
    print(f"  Push:         {actual_push} ({actual_push/len(y_relevant)*100:.1f}%)")

    # Model predictions
    print(f"\n" + "="*60)
    print("MODEL BETTING STRATEGY")
    print("="*60)

    # Test different confidence thresholds
    thresholds = [0.0, 0.25, 0.5, 0.75]

    for threshold in thresholds:
        print(f"\n{'='*60}")
        print(f"Confidence Threshold: {threshold} (bet if |prediction - line| > {threshold})")
        print(f"{'='*60}")

        confidence = np.abs(pred_relevant - line)
        confident_bets = confidence > threshold

        if confident_bets.sum() == 0:
            print("No bets at this threshold")
            continue

        # Split into over and under predictions
        over_bets = (pred_relevant > line) & confident_bets
        under_bets = (pred_relevant < line) & confident_bets

        # Calculate accuracy
        over_correct = ((y_relevant > line) & over_bets).sum()
        under_correct = ((y_relevant < line) & under_bets).sum()

        total_bets = over_bets.sum() + under_bets.sum()
        total_correct = over_correct + under_correct

        if total_bets == 0:
            continue

        overall_accuracy = total_correct / total_bets

        print(f"\nBetting Summary:")
        print(f"  Total bets: {total_bets}")
        print(f"  Over bets:  {over_bets.sum()}")
        print(f"  Under bets: {under_bets.sum()}")

        print(f"\nResults:")
        if over_bets.sum() > 0:
            over_acc = over_correct / over_bets.sum()
            print(f"  Over accuracy:  {over_acc*100:.1f}% ({over_correct}/{over_bets.sum()})")
        else:
            over_acc = 0
            print(f"  Over accuracy:  N/A")

        if under_bets.sum() > 0:
            under_acc = under_correct / under_bets.sum()
            print(f"  Under accuracy: {under_acc*100:.1f}% ({under_correct}/{under_bets.sum()})")
        else:
            under_acc = 0
            print(f"  Under accuracy: N/A")

        print(f"  Overall accuracy: {overall_accuracy*100:.1f}% ({total_correct}/{total_bets})")

        # Profitability calculation (assuming -110 on both sides for simplicity)
        print(f"\nProfitability (assuming -110 odds on both sides):")
        units_won = total_correct * 0.909  # Win $0.909 per $1 bet at -110
        units_lost = (total_bets - total_correct) * 1.0  # Lose $1 per $1 bet
        net_profit = units_won - units_lost
        roi = (net_profit / total_bets) * 100

        print(f"  Units won:  {units_won:.2f}")
        print(f"  Units lost: {units_lost:.2f}")
        print(f"  Net profit: {net_profit:+.2f} units")
        print(f"  ROI:        {roi:+.1f}%")

        # Break-even check
        breakeven_rate = 0.524  # Need 52.4% to beat -110 vig
        if overall_accuracy > breakeven_rate:
            edge = (overall_accuracy - breakeven_rate) * 100
            print(f"  ✓ PROFITABLE! ({edge:.1f}% above break-even)")
        else:
            edge = (overall_accuracy - breakeven_rate) * 100
            print(f"  ✗ NOT PROFITABLE ({edge:.1f}% below break-even)")

    # Show some example bets
    print(f"\n" + "="*60)
    print("EXAMPLE PREDICTIONS")
    print("="*60)

    # Take 10 random examples where model was confident
    confident_mask = np.abs(pred_relevant - line) > 0.5
    if confident_mask.sum() > 0:
        sample_indices = np.random.choice(np.where(confident_mask)[0], min(10, confident_mask.sum()), replace=False)

        print(f"\n{'Predicted':<12} {'Actual':<10} {'Result':<10} {'Confidence':<12}")
        print("-" * 50)
        for idx in sample_indices:
            pred = pred_relevant.iloc[idx]
            actual = y_relevant.iloc[idx]

            if pred > line:
                predicted_outcome = f"Over {line}"
                correct = actual > line
            else:
                predicted_outcome = f"Under {line}"
                correct = actual < line

            result = "✓ WIN" if correct else "✗ LOSS"
            confidence = abs(pred - line)

            print(f"{predicted_outcome:<12} {actual:<10.0f} {result:<10} {confidence:<12.2f}")


def main():
    """Main testing pipeline."""
    print("="*60)
    print("BETTING LINE ACCURACY TEST")
    print("="*60)
    print("\nTesting model performance on 2.5 shot line")
    print("Using 2025-2026 season data")

    test_line_accuracy(line=2.5)

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()