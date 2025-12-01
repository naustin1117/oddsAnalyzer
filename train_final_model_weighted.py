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

    # Convert game_date to datetime for weighting
    train_df['game_date'] = pd.to_datetime(train_df['game_date'])

    print(f"\nFinal split:")
    print(f"  Train set: {len(train_df)} rows (2023-2024 + 2024-2025)")
    print(f"  Test set: {len(test_df)} rows (2025-2026)")

    # Calculate exponential weights
    print("\n" + "="*60)
    print("CALCULATING EXPONENTIAL WEIGHTS")
    print("="*60)

    max_date = train_df['game_date'].max()
    train_df['days_old'] = (max_date - train_df['game_date']).dt.days

    # Exponential decay with 180-day half-life
    # A game from 180 days ago gets weight = 0.5
    # A game from 360 days ago gets weight = 0.25
    # A game from 720 days ago (2 years) gets weight = 0.0625
    half_life_days = 180
    train_df['sample_weight'] = 0.5 ** (train_df['days_old'] / half_life_days)

    print(f"\nWeight statistics:")
    print(f"  Half-life: {half_life_days} days")
    print(f"  Most recent game: weight = {train_df['sample_weight'].max():.4f}")
    print(f"  Oldest game: weight = {train_df['sample_weight'].min():.6f}")
    print(f"  Mean weight: {train_df['sample_weight'].mean():.4f}")
    print(f"  Median weight: {train_df['sample_weight'].median():.4f}")

    # Show weight distribution by age
    print(f"\nWeight distribution by age:")
    print(f"  0-90 days old:    avg weight = {train_df[train_df['days_old'] <= 90]['sample_weight'].mean():.4f}")
    print(f"  90-180 days old:  avg weight = {train_df[(train_df['days_old'] > 90) & (train_df['days_old'] <= 180)]['sample_weight'].mean():.4f}")
    print(f"  180-365 days old: avg weight = {train_df[(train_df['days_old'] > 180) & (train_df['days_old'] <= 365)]['sample_weight'].mean():.4f}")
    print(f"  365-730 days old: avg weight = {train_df[(train_df['days_old'] > 365) & (train_df['days_old'] <= 730)]['sample_weight'].mean():.4f}")
    print(f"  730+ days old:    avg weight = {train_df[train_df['days_old'] > 730]['sample_weight'].mean():.4f}")

    # Show data distribution by season
    print(f"\nData age distribution:")
    season_2024_2025_count = len(train_df[train_df['days_old'] <= 365])
    season_2023_2024_count = len(train_df[train_df['days_old'] > 365])
    print(f"  2024-2025 season (~0-365 days old): {season_2024_2025_count} rows ({season_2024_2025_count/len(train_df)*100:.1f}%)")
    print(f"  2023-2024 season (~365-730 days old): {season_2023_2024_count} rows ({season_2023_2024_count/len(train_df)*100:.1f}%)")

    # Define features
    exclude_cols = [
        'player_id', 'game_id', 'season_id', 'game_type', 'game_date',
        'team_abbrev', 'opponent_abbrev', 'position_code',
        'shots',
        'goals', 'assists', 'points', 'plus_minus',
        'power_play_goals', 'power_play_points',
        'shorthanded_goals', 'shorthanded_points',
        'pim', 'shifts', 'toi_raw',
        'toi_minutes',
        'days_old', 'sample_weight'  # Exclude our helper columns
    ]

    feature_cols = [col for col in train_df.columns if col not in exclude_cols]
    print(f"\nFeatures ({len(feature_cols)}): {feature_cols}")

    # Prepare datasets
    X_train = train_df[feature_cols]
    y_train = train_df['shots']
    sample_weights = train_df['sample_weight']

    X_test = test_df[feature_cols]
    y_test = test_df['shots']

    # Remove NaN rows
    train_mask = ~(X_train.isna().any(axis=1) | y_train.isna())
    X_train = X_train[train_mask]
    y_train = y_train[train_mask]
    sample_weights = sample_weights[train_mask]

    test_mask = ~(X_test.isna().any(axis=1) | y_test.isna())
    X_test = X_test[test_mask]
    y_test = y_test[test_mask]

    print(f"\nAfter removing NaN:")
    print(f"  Train set: {len(X_train)} rows")
    print(f"  Test set: {len(X_test)} rows")

    return X_train, y_train, X_test, y_test, sample_weights, feature_cols


def train_models(X_train, y_train, X_test, y_test, sample_weights, feature_cols):
    """Train models with and without exponential weighting."""

    # Baseline
    last10_pred = X_test['shots_last10_avg'].values
    baseline_r2 = r2_score(y_test, last10_pred)
    baseline_mae = mean_absolute_error(y_test, last10_pred)

    print("\n" + "="*60)
    print("MODEL WITHOUT WEIGHTING")
    print("="*60)

    # Train without weights
    lgb_unweighted = lgb.LGBMRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        num_leaves=15,
        min_child_samples=20,
        random_state=42,
        n_jobs=-1,
        verbose=-1
    )

    print("\nTraining model without weights...")
    lgb_unweighted.fit(X_train, y_train)

    lgb_unweighted_pred = lgb_unweighted.predict(X_test)
    lgb_unweighted_mae = mean_absolute_error(y_test, lgb_unweighted_pred)
    lgb_unweighted_r2 = r2_score(y_test, lgb_unweighted_pred)

    print(f"\nLightGBM (Unweighted):")
    print(f"  MAE:  {lgb_unweighted_mae:.4f}")
    print(f"  R²:   {lgb_unweighted_r2:.4f}")

    print("\n" + "="*60)
    print("MODEL WITH EXPONENTIAL WEIGHTING")
    print("="*60)

    # Train with weights
    lgb_weighted = lgb.LGBMRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        num_leaves=15,
        min_child_samples=20,
        random_state=42,
        n_jobs=-1,
        verbose=-1
    )

    print("\nTraining model with exponential weighting...")
    lgb_weighted.fit(X_train, y_train, sample_weight=sample_weights)

    lgb_weighted_pred = lgb_weighted.predict(X_test)
    lgb_weighted_mae = mean_absolute_error(y_test, lgb_weighted_pred)
    lgb_weighted_r2 = r2_score(y_test, lgb_weighted_pred)

    print(f"\nLightGBM (Weighted):")
    print(f"  MAE:  {lgb_weighted_mae:.4f}")
    print(f"  R²:   {lgb_weighted_r2:.4f}")

    # Comparison
    print("\n" + "="*60)
    print("COMPARISON")
    print("="*60)

    print(f"\n{'Model':<30} {'MAE':>10} {'R²':>10} {'Change':>10}")
    print("-" * 65)
    print(f"{'Baseline (Last10)':<30} {baseline_mae:>10.4f} {baseline_r2:>10.4f} {'-':>10}")
    print(f"{'LightGBM (Unweighted)':<30} {lgb_unweighted_mae:>10.4f} {lgb_unweighted_r2:>10.4f} {'-':>10}")

    r2_change = lgb_weighted_r2 - lgb_unweighted_r2
    mae_change = lgb_weighted_mae - lgb_unweighted_mae

    print(f"{'LightGBM (Weighted)':<30} {lgb_weighted_mae:>10.4f} {lgb_weighted_r2:>10.4f} {r2_change:>+10.4f}")

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    r2_pct = (r2_change / lgb_unweighted_r2) * 100 if lgb_unweighted_r2 != 0 else 0
    mae_pct = (mae_change / lgb_unweighted_mae) * 100 if lgb_unweighted_mae != 0 else 0

    print(f"\nR² change:   {r2_change:+.4f} ({r2_pct:+.1f}%)")
    print(f"MAE change:  {mae_change:+.4f} ({mae_pct:+.1f}%)")

    if r2_change > 0.001:
        print(f"\n✓ Exponential weighting IMPROVED performance!")
        print(f"  Old data (2023-2024) was hurting the model")
        print(f"  Weighting helped focus on recent patterns")
    elif r2_change < -0.001:
        print(f"\n✗ Exponential weighting HURT performance")
        print(f"  Old data still contains useful signal")
    else:
        print(f"\n~ Exponential weighting had NO significant impact")

    # Feature importance comparison
    print("\n" + "="*60)
    print("FEATURE IMPORTANCE COMPARISON")
    print("="*60)

    importance_unweighted = pd.DataFrame({
        'feature': feature_cols,
        'unweighted': lgb_unweighted.feature_importances_,
        'weighted': lgb_weighted.feature_importances_
    }).sort_values('unweighted', ascending=False)

    importance_unweighted['diff'] = importance_unweighted['weighted'] - importance_unweighted['unweighted']

    print("\nTop features (ranked by unweighted importance):")
    print(f"{'Feature':<35} {'Unweighted':>12} {'Weighted':>12} {'Diff':>10}")
    print("-" * 72)
    for idx, row in importance_unweighted.head(10).iterrows():
        print(f"{row['feature']:<35} {row['unweighted']:>12.1f} {row['weighted']:>12.1f} {row['diff']:>+10.1f}")

    return lgb_weighted if r2_change > 0 else lgb_unweighted


def main():
    """Main training pipeline."""
    print("="*60)
    print("EXPONENTIAL WEIGHTING TEST (2+ YEAR OLD DATA)")
    print("="*60)
    print("\nTraining on: 2023-2024 + 2024-2025 seasons")
    print("Testing on:  2025-2026 season (current)")
    print("\nHypothesis: 2-year-old data should be down-weighted")

    # Load data
    X_train, y_train, X_test, y_test, sample_weights, feature_cols = load_and_prepare_data()

    # Train and compare
    best_model = train_models(X_train, y_train, X_test, y_test, sample_weights, feature_cols)

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()