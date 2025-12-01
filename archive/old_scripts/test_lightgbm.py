import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, r2_score
import lightgbm as lgb
import xgboost as xgb


def load_data():
    """Load training and test data."""
    print("Loading data...")

    # Load both seasons
    season_2023_2024 = pd.read_csv('data/player_game_logs_2023_2024_with_opponent.csv')
    season_2024_2025 = pd.read_csv('data/player_game_logs_2024_2025_with_opponent.csv')

    # Sort 2024-2025 by date and split in half
    season_2024_2025['game_date'] = pd.to_datetime(season_2024_2025['game_date'])
    season_2024_2025 = season_2024_2025.sort_values('game_date').reset_index(drop=True)

    midpoint_idx = len(season_2024_2025) // 2
    midpoint_date = season_2024_2025.loc[midpoint_idx, 'game_date']

    first_half_2024_2025 = season_2024_2025[season_2024_2025['game_date'] < midpoint_date].copy()
    second_half_2024_2025 = season_2024_2025[season_2024_2025['game_date'] >= midpoint_date].copy()

    train_df = pd.concat([season_2023_2024, first_half_2024_2025], ignore_index=True)
    test_df = second_half_2024_2025

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
    X_test = test_df[feature_cols]
    y_test = test_df['shots']

    # Remove NaN
    train_mask = ~(X_train.isna().any(axis=1) | y_train.isna())
    X_train = X_train[train_mask]
    y_train = y_train[train_mask]

    test_mask = ~(X_test.isna().any(axis=1) | y_test.isna())
    X_test = X_test[test_mask]
    y_test = y_test[test_mask]

    print(f"Train: {len(X_train)} rows, Test: {len(X_test)} rows")
    return X_train, y_train, X_test, y_test


def main():
    print("="*60)
    print("LIGHTGBM QUICK TEST")
    print("="*60)

    X_train, y_train, X_test, y_test = load_data()

    # Baseline
    last10_pred = X_test['shots_last10_avg'].values
    baseline_r2 = r2_score(y_test, last10_pred)
    baseline_mae = mean_absolute_error(y_test, last10_pred)

    print(f"\n{'Model':<30} {'MAE':>10} {'R²':>10}")
    print("-" * 52)
    print(f"{'Baseline (Last10 Avg)':<30} {baseline_mae:>10.4f} {baseline_r2:>10.4f}")

    # Tuned XGBoost (from previous experiment)
    print("\n" + "="*60)
    print("TUNED XGBOOST (from previous run)")
    print("="*60)
    xgb_tuned = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        min_child_weight=1,
        random_state=42,
        n_jobs=-1
    )
    xgb_tuned.fit(X_train, y_train, verbose=False)
    xgb_pred = xgb_tuned.predict(X_test)
    xgb_mae = mean_absolute_error(y_test, xgb_pred)
    xgb_r2 = r2_score(y_test, xgb_pred)
    print(f"{'XGBoost (tuned)':<30} {xgb_mae:>10.4f} {xgb_r2:>10.4f}")

    # LightGBM with default parameters
    print("\n" + "="*60)
    print("LIGHTGBM - DEFAULT PARAMS")
    print("="*60)
    lgb_default = lgb.LGBMRegressor(
        random_state=42,
        n_jobs=-1,
        verbose=-1
    )
    lgb_default.fit(X_train, y_train)
    lgb_default_pred = lgb_default.predict(X_test)
    lgb_default_mae = mean_absolute_error(y_test, lgb_default_pred)
    lgb_default_r2 = r2_score(y_test, lgb_default_pred)
    print(f"{'LightGBM (default)':<30} {lgb_default_mae:>10.4f} {lgb_default_r2:>10.4f}")

    # LightGBM with XGBoost-like parameters
    print("\n" + "="*60)
    print("LIGHTGBM - TUNED PARAMS (XGBoost-like)")
    print("="*60)
    lgb_tuned = lgb.LGBMRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        num_leaves=15,  # LightGBM uses num_leaves instead of max_depth
        min_child_samples=20,  # Similar to min_child_weight
        random_state=42,
        n_jobs=-1,
        verbose=-1
    )
    lgb_tuned.fit(X_train, y_train)
    lgb_tuned_pred = lgb_tuned.predict(X_test)
    lgb_tuned_mae = mean_absolute_error(y_test, lgb_tuned_pred)
    lgb_tuned_r2 = r2_score(y_test, lgb_tuned_pred)
    print(f"{'LightGBM (tuned)':<30} {lgb_tuned_mae:>10.4f} {lgb_tuned_r2:>10.4f}")

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"\n{'Model':<30} {'MAE':>10} {'R²':>10} {'vs XGBoost':>12}")
    print("-" * 65)
    print(f"{'Baseline (Last10)':<30} {baseline_mae:>10.4f} {baseline_r2:>10.4f} {'-':>12}")
    print(f"{'XGBoost (tuned)':<30} {xgb_mae:>10.4f} {xgb_r2:>10.4f} {'-':>12}")

    lgb_default_diff = lgb_default_r2 - xgb_r2
    lgb_tuned_diff = lgb_tuned_r2 - xgb_r2

    print(f"{'LightGBM (default)':<30} {lgb_default_mae:>10.4f} {lgb_default_r2:>10.4f} {lgb_default_diff:>+12.4f}")
    print(f"{'LightGBM (tuned)':<30} {lgb_tuned_mae:>10.4f} {lgb_tuned_r2:>10.4f} {lgb_tuned_diff:>+12.4f}")

    # Verdict
    print("\n" + "="*60)
    print("VERDICT")
    print("="*60)

    best_r2 = max(xgb_r2, lgb_default_r2, lgb_tuned_r2)

    if lgb_tuned_r2 == best_r2:
        print(f"\n✓ LightGBM (tuned) is BEST: R²={lgb_tuned_r2:.4f}")
        improvement = ((lgb_tuned_r2 - xgb_r2) / xgb_r2) * 100
        print(f"  Improvement over XGBoost: {improvement:+.1f}%")
    elif lgb_default_r2 == best_r2:
        print(f"\n✓ LightGBM (default) is BEST: R²={lgb_default_r2:.4f}")
        improvement = ((lgb_default_r2 - xgb_r2) / xgb_r2) * 100
        print(f"  Improvement over XGBoost: {improvement:+.1f}%")
    else:
        print(f"\n✓ XGBoost (tuned) is still BEST: R²={xgb_r2:.4f}")
        print(f"  LightGBM did not improve performance")

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
