import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, r2_score
import lightgbm as lgb


def load_and_prepare_data():
    """Load all historical data for training and current season for testing."""
    print("Loading data...")

    # Load all seasons
    season_2023_2024 = pd.read_csv('data/player_game_logs_2023_2024_with_opponent.csv')
    season_2024_2025 = pd.read_csv('data/player_game_logs_2024_2025_with_opponent.csv')
    season_2025_2026 = pd.read_csv('data/player_game_logs_2025_2026_with_opponent.csv')

    print(f"2023-2024 season: {len(season_2023_2024)} rows")
    print(f"2024-2025 season: {len(season_2024_2025)} rows")
    print(f"2025-2026 season: {len(season_2025_2026)} rows")

    # Training: All historical data (2023-2024 + 2024-2025)
    train_df = pd.concat([season_2023_2024, season_2024_2025], ignore_index=True)
    test_df = season_2025_2026

    print(f"\nFinal split:")
    print(f"  Train set: {len(train_df)} rows (2023-2024 + 2024-2025)")
    print(f"  Test set: {len(test_df)} rows (2025-2026)")

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
    print(f"\nFeatures ({len(feature_cols)}): {feature_cols}")

    # Prepare datasets
    X_train = train_df[feature_cols]
    y_train = train_df['shots']

    X_test = test_df[feature_cols]
    y_test = test_df['shots']

    # Remove NaN rows
    train_mask = ~(X_train.isna().any(axis=1) | y_train.isna())
    X_train = X_train[train_mask]
    y_train = y_train[train_mask]

    test_mask = ~(X_test.isna().any(axis=1) | y_test.isna())
    X_test = X_test[test_mask]
    y_test = y_test[test_mask]

    print(f"\nAfter removing NaN:")
    print(f"  Train set: {len(X_train)} rows")
    print(f"  Test set: {len(X_test)} rows")

    return X_train, y_train, X_test, y_test, feature_cols


def train_final_model(X_train, y_train, X_test, y_test, feature_cols):
    """Train the best model on all historical data and evaluate on current season."""

    print("\n" + "="*60)
    print("TRAINING FINAL MODEL")
    print("="*60)

    # Baseline
    last10_pred = X_test['shots_last10_avg'].values
    baseline_r2 = r2_score(y_test, last10_pred)
    baseline_mae = mean_absolute_error(y_test, last10_pred)

    print(f"\n{'Model':<30} {'MAE':>10} {'R²':>10}")
    print("-" * 52)
    print(f"{'Baseline (Last10 Avg)':<30} {baseline_mae:>10.4f} {baseline_r2:>10.4f}")

    # Train LightGBM with best hyperparameters
    print("\n" + "="*60)
    print("TRAINING LIGHTGBM (Tuned Hyperparameters)")
    print("="*60)
    print("\nHyperparameters:")
    print("  n_estimators: 200")
    print("  max_depth: 4")
    print("  learning_rate: 0.05")
    print("  num_leaves: 15")
    print("  min_child_samples: 20")

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

    print("\nTraining model...")
    lgb_model.fit(X_train, y_train)
    print("✓ Training complete")

    # Evaluate
    print("\n" + "="*60)
    print("EVALUATION ON 2025-2026 SEASON")
    print("="*60)

    lgb_pred = lgb_model.predict(X_test)
    lgb_mae = mean_absolute_error(y_test, lgb_pred)
    lgb_r2 = r2_score(y_test, lgb_pred)

    print(f"\n{'LightGBM (Final Model)':<30} {lgb_mae:>10.4f} {lgb_r2:>10.4f}")

    # Feature importance
    print("\n" + "="*60)
    print("FEATURE IMPORTANCE")
    print("="*60)

    importance_df = pd.DataFrame({
        'feature': feature_cols,
        'importance': lgb_model.feature_importances_
    }).sort_values('importance', ascending=False)

    print("\nTop 10 most important features:")
    for idx, row in importance_df.head(10).iterrows():
        print(f"  {row['feature']:35s}: {row['importance']:.4f}")

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    improvement_vs_baseline = ((baseline_mae - lgb_mae) / baseline_mae) * 100

    print(f"\nBaseline MAE: {baseline_mae:.4f}")
    print(f"Model MAE:    {lgb_mae:.4f}")
    print(f"Improvement:  {improvement_vs_baseline:.1f}%")
    print(f"\nModel R²:     {lgb_r2:.4f}")
    print(f"Baseline R²:  {baseline_r2:.4f}")

    # Prediction distribution
    print("\n" + "="*60)
    print("PREDICTION ANALYSIS")
    print("="*60)

    pred_std = np.std(lgb_pred)
    actual_std = np.std(y_test)

    print(f"\nActual shots statistics:")
    print(f"  Mean: {np.mean(y_test):.2f}")
    print(f"  Std:  {actual_std:.2f}")
    print(f"  Min:  {np.min(y_test):.0f}")
    print(f"  Max:  {np.max(y_test):.0f}")

    print(f"\nPredicted shots statistics:")
    print(f"  Mean: {np.mean(lgb_pred):.2f}")
    print(f"  Std:  {pred_std:.2f}")
    print(f"  Min:  {np.min(lgb_pred):.2f}")
    print(f"  Max:  {np.max(lgb_pred):.2f}")

    # Error analysis
    errors = np.abs(y_test - lgb_pred)
    print(f"\nPrediction errors:")
    print(f"  Mean Absolute Error: {np.mean(errors):.4f}")
    print(f"  Median Absolute Error: {np.median(errors):.4f}")
    print(f"  90th percentile: {np.percentile(errors, 90):.2f}")

    return lgb_model


def main():
    """Main training pipeline."""
    print("="*60)
    print("FINAL MODEL TRAINING")
    print("="*60)
    print("\nTraining on: 2023-2024 + 2024-2025 seasons")
    print("Testing on:  2025-2026 season (current)")

    # Load data
    X_train, y_train, X_test, y_test, feature_cols = load_and_prepare_data()

    # Train and evaluate
    model = train_final_model(X_train, y_train, X_test, y_test, feature_cols)

    print("\n" + "="*60)
    print("TRAINING COMPLETE")
    print("="*60)
    print("\n✓ Model ready for predictions on 2025-2026 season")


if __name__ == "__main__":
    main()
