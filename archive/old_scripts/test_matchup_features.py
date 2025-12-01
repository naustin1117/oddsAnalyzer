import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, r2_score
import lightgbm as lgb


def load_data():
    """Load data with matchup features."""
    print("Loading data with matchup features...")

    # Load both seasons
    season_2023_2024 = pd.read_csv('data/player_game_logs_2023_2024_with_matchup.csv')
    season_2024_2025 = pd.read_csv('data/player_game_logs_2024_2025_with_matchup.csv')

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
    print(f"Features ({len(feature_cols)}): {feature_cols}")

    return X_train, y_train, X_test, y_test, feature_cols


def main():
    print("="*60)
    print("TESTING MATCHUP HISTORY FEATURES")
    print("="*60)

    X_train, y_train, X_test, y_test, feature_cols = load_data()

    # Baseline
    last10_pred = X_test['shots_last10_avg'].values
    baseline_r2 = r2_score(y_test, last10_pred)
    baseline_mae = mean_absolute_error(y_test, last10_pred)

    print(f"\n{'Model':<35} {'MAE':>10} {'R²':>10} {'vs Previous':>12}")
    print("-" * 70)
    print(f"{'Baseline (Last10)':<35} {baseline_mae:>10.4f} {baseline_r2:>10.4f} {'-':>12}")

    # Previous best (WITHOUT matchup features)
    print("\n" + "="*60)
    print("PREVIOUS BEST (without matchup features)")
    print("="*60)
    print(f"{'LightGBM (21 features)':<35} {'1.0158':>10} {'0.1959':>10} {'-':>12}")

    # LightGBM WITH matchup feature
    print("\n" + "="*60)
    print("NEW MODEL (with matchup_shots_avg only)")
    print("="*60)

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
    lgb_pred = lgb_model.predict(X_test)
    lgb_mae = mean_absolute_error(y_test, lgb_pred)
    lgb_r2 = r2_score(y_test, lgb_pred)

    r2_improvement = lgb_r2 - 0.1959  # vs previous best

    print(f"{'LightGBM (22 features)':<35} {lgb_mae:>10.4f} {lgb_r2:>10.4f} {r2_improvement:>+12.4f}")

    # Feature importance for matchup features
    print("\n" + "="*60)
    print("MATCHUP FEATURE IMPORTANCE")
    print("="*60)

    importance_df = pd.DataFrame({
        'feature': feature_cols,
        'importance': lgb_model.feature_importances_
    }).sort_values('importance', ascending=False)

    print("\nAll features ranked:")
    for idx, row in importance_df.iterrows():
        marker = " ← NEW" if 'matchup' in row['feature'] else ""
        print(f"  {row['feature']:35s}: {row['importance']:.4f}{marker}")

    # Summary
    print("\n" + "="*60)
    print("VERDICT")
    print("="*60)

    improvement_pct = (r2_improvement / 0.1959) * 100

    if r2_improvement > 0.001:
        print(f"\n✓ Matchup feature IMPROVED performance!")
        print(f"  R² increased from 0.1959 to {lgb_r2:.4f}")
        print(f"  Improvement: {r2_improvement:+.4f} ({improvement_pct:+.1f}%)")
    elif r2_improvement < -0.001:
        print(f"\n✗ Matchup feature HURT performance")
        print(f"  R² decreased from 0.1959 to {lgb_r2:.4f}")
        print(f"  Change: {r2_improvement:.4f} ({improvement_pct:.1f}%)")
    else:
        print(f"\n~ Matchup feature had NO significant impact")
        print(f"  R² stayed at ~0.196")

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()