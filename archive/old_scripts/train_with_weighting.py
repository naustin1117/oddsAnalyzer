import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb


def load_and_prepare_data():
    """Load training and test data with sample weights."""
    print("Loading data...")

    # Load both seasons
    season_2023_2024 = pd.read_csv('data/player_game_logs_2023_2024_with_opponent.csv')
    season_2024_2025 = pd.read_csv('data/player_game_logs_2024_2025_with_opponent.csv')

    print(f"2023-2024 season: {len(season_2023_2024)} rows")
    print(f"2024-2025 season: {len(season_2024_2025)} rows")

    # Sort 2024-2025 by date and split in half
    season_2024_2025['game_date'] = pd.to_datetime(season_2024_2025['game_date'])
    season_2024_2025 = season_2024_2025.sort_values('game_date').reset_index(drop=True)

    # Find midpoint
    midpoint_idx = len(season_2024_2025) // 2
    midpoint_date = season_2024_2025.loc[midpoint_idx, 'game_date']

    first_half_2024_2025 = season_2024_2025[season_2024_2025['game_date'] < midpoint_date].copy()
    second_half_2024_2025 = season_2024_2025[season_2024_2025['game_date'] >= midpoint_date].copy()

    print(f"\n2024-2025 split at: {midpoint_date.strftime('%Y-%m-%d')}")

    # Combine training data
    train_df = pd.concat([season_2023_2024, first_half_2024_2025], ignore_index=True)
    test_df = second_half_2024_2025

    # Convert train dates to datetime
    train_df['game_date'] = pd.to_datetime(train_df['game_date'])

    print(f"\nFinal split:")
    print(f"  Train set: {len(train_df)} rows")
    print(f"  Test set: {len(test_df)} rows")

    # Calculate exponential weights based on game date
    print("\n" + "="*60)
    print("CALCULATING EXPONENTIAL WEIGHTS")
    print("="*60)

    max_date = train_df['game_date'].max()
    train_df['days_old'] = (max_date - train_df['game_date']).dt.days

    # Exponential decay with 180-day half-life
    # This means a game from 180 days ago gets weight = 0.5
    # A game from 360 days ago gets weight = 0.25
    half_life_days = 180
    train_df['sample_weight'] = 0.5 ** (train_df['days_old'] / half_life_days)

    print(f"\nWeight statistics:")
    print(f"  Half-life: {half_life_days} days")
    print(f"  Most recent game: weight = {train_df['sample_weight'].max():.4f}")
    print(f"  Oldest game: weight = {train_df['sample_weight'].min():.4f}")
    print(f"  Mean weight: {train_df['sample_weight'].mean():.4f}")
    print(f"  Median weight: {train_df['sample_weight'].median():.4f}")

    # Show weight distribution
    print(f"\nWeight distribution by age:")
    print(f"  0-90 days old:   avg weight = {train_df[train_df['days_old'] <= 90]['sample_weight'].mean():.4f}")
    print(f"  90-180 days old: avg weight = {train_df[(train_df['days_old'] > 90) & (train_df['days_old'] <= 180)]['sample_weight'].mean():.4f}")
    print(f"  180-365 days old: avg weight = {train_df[(train_df['days_old'] > 180) & (train_df['days_old'] <= 365)]['sample_weight'].mean():.4f}")
    print(f"  365+ days old:   avg weight = {train_df[train_df['days_old'] > 365]['sample_weight'].mean():.4f}")

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


def train_models(X_train, y_train, X_test, y_test, sample_weights):
    """Train models with and without exponential weighting."""

    results = {}

    # Baseline
    last10_pred = X_test['shots_last10_avg'].values
    last10_mae = mean_absolute_error(y_test, last10_pred)
    last10_r2 = r2_score(y_test, last10_pred)
    results['baseline'] = {'mae': last10_mae, 'r2': last10_r2}

    print("\n" + "="*60)
    print("MODELS WITHOUT WEIGHTING (Original)")
    print("="*60)

    # Ridge without weights
    ridge_orig = Ridge(alpha=1.0)
    ridge_orig.fit(X_train, y_train)

    ridge_orig_pred = ridge_orig.predict(X_test)
    ridge_orig_mae = mean_absolute_error(y_test, ridge_orig_pred)
    ridge_orig_r2 = r2_score(y_test, ridge_orig_pred)

    print(f"\nRidge Regression:")
    print(f"  MAE:  {ridge_orig_mae:.4f}")
    print(f"  R²:   {ridge_orig_r2:.4f}")

    results['ridge_orig'] = {'mae': ridge_orig_mae, 'r2': ridge_orig_r2}

    # XGBoost without weights
    xgb_orig = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        n_jobs=-1
    )
    xgb_orig.fit(X_train, y_train, verbose=False)

    xgb_orig_pred = xgb_orig.predict(X_test)
    xgb_orig_mae = mean_absolute_error(y_test, xgb_orig_pred)
    xgb_orig_r2 = r2_score(y_test, xgb_orig_pred)

    print(f"\nXGBoost:")
    print(f"  MAE:  {xgb_orig_mae:.4f}")
    print(f"  R²:   {xgb_orig_r2:.4f}")

    results['xgb_orig'] = {'mae': xgb_orig_mae, 'r2': xgb_orig_r2}

    print("\n" + "="*60)
    print("MODELS WITH EXPONENTIAL WEIGHTING")
    print("="*60)

    # Ridge with weights
    ridge_weighted = Ridge(alpha=1.0)
    ridge_weighted.fit(X_train, y_train, sample_weight=sample_weights)

    ridge_weighted_pred = ridge_weighted.predict(X_test)
    ridge_weighted_mae = mean_absolute_error(y_test, ridge_weighted_pred)
    ridge_weighted_r2 = r2_score(y_test, ridge_weighted_pred)

    print(f"\nRidge Regression (Weighted):")
    print(f"  MAE:  {ridge_weighted_mae:.4f}")
    print(f"  R²:   {ridge_weighted_r2:.4f}")

    results['ridge_weighted'] = {'mae': ridge_weighted_mae, 'r2': ridge_weighted_r2}

    # XGBoost with weights
    xgb_weighted = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        n_jobs=-1
    )
    xgb_weighted.fit(X_train, y_train, sample_weight=sample_weights, verbose=False)

    xgb_weighted_pred = xgb_weighted.predict(X_test)
    xgb_weighted_mae = mean_absolute_error(y_test, xgb_weighted_pred)
    xgb_weighted_r2 = r2_score(y_test, xgb_weighted_pred)

    print(f"\nXGBoost (Weighted):")
    print(f"  MAE:  {xgb_weighted_mae:.4f}")
    print(f"  R²:   {xgb_weighted_r2:.4f}")

    results['xgb_weighted'] = {'mae': xgb_weighted_mae, 'r2': xgb_weighted_r2}

    return results


def compare_results(results):
    """Compare weighted vs unweighted performance."""
    print("\n" + "="*60)
    print("COMPARISON: WEIGHTING IMPACT")
    print("="*60)

    print(f"\n{'Model':<25} {'MAE':>10} {'R²':>10} {'Change':>10}")
    print("-" * 60)

    # Baseline
    print(f"{'Baseline (Last10)':<25} {results['baseline']['mae']:>10.4f} {results['baseline']['r2']:>10.4f} {'-':>10}")

    # Ridge
    ridge_mae_change = results['ridge_weighted']['mae'] - results['ridge_orig']['mae']
    ridge_r2_change = results['ridge_weighted']['r2'] - results['ridge_orig']['r2']

    print(f"\n{'Ridge (Original)':<25} {results['ridge_orig']['mae']:>10.4f} {results['ridge_orig']['r2']:>10.4f} {'-':>10}")
    print(f"{'Ridge (Weighted)':<25} {results['ridge_weighted']['mae']:>10.4f} {results['ridge_weighted']['r2']:>10.4f} {ridge_r2_change:>+10.4f}")

    # XGBoost
    xgb_mae_change = results['xgb_weighted']['mae'] - results['xgb_orig']['mae']
    xgb_r2_change = results['xgb_weighted']['r2'] - results['xgb_orig']['r2']

    print(f"\n{'XGBoost (Original)':<25} {results['xgb_orig']['mae']:>10.4f} {results['xgb_orig']['r2']:>10.4f} {'-':>10}")
    print(f"{'XGBoost (Weighted)':<25} {results['xgb_weighted']['mae']:>10.4f} {results['xgb_weighted']['r2']:>10.4f} {xgb_r2_change:>+10.4f}")

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    ridge_pct = (ridge_r2_change / results['ridge_orig']['r2']) * 100 if results['ridge_orig']['r2'] != 0 else 0
    xgb_pct = (xgb_r2_change / results['xgb_orig']['r2']) * 100 if results['xgb_orig']['r2'] != 0 else 0

    print(f"\nRidge R² change:   {ridge_r2_change:+.4f} ({ridge_pct:+.1f}%)")
    print(f"XGBoost R² change: {xgb_r2_change:+.4f} ({xgb_pct:+.1f}%)")

    if ridge_r2_change > 0 or xgb_r2_change > 0:
        print("\n✓ Exponential weighting IMPROVED performance!")
    else:
        print("\n✗ Exponential weighting did not improve performance")


def main():
    """Main training pipeline."""
    print("="*60)
    print("EXPONENTIAL WEIGHTING EXPERIMENT")
    print("="*60)

    # Load data with weights
    X_train, y_train, X_test, y_test, sample_weights, feature_cols = load_and_prepare_data()

    # Train and compare
    results = train_models(X_train, y_train, X_test, y_test, sample_weights)

    # Show comparison
    compare_results(results)

    print("\n" + "="*60)
    print("EXPERIMENT COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()