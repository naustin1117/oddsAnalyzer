import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
import xgboost as xgb
import time


def load_and_prepare_data():
    """Load training and test data."""
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

    print(f"\nFinal split:")
    print(f"  Train set: {len(train_df)} rows")
    print(f"  Test set: {len(test_df)} rows")

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


def tune_ridge(X_train, y_train):
    """Tune Ridge regression hyperparameters."""
    print("\n" + "="*60)
    print("TUNING RIDGE REGRESSION")
    print("="*60)

    # Parameter grid
    param_grid = {
        'alpha': [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0]
    }

    print(f"\nParameter grid:")
    print(f"  alpha: {param_grid['alpha']}")

    # Time-series cross-validation (respects temporal order)
    tscv = TimeSeriesSplit(n_splits=5)

    print(f"\nUsing TimeSeriesSplit with {tscv.n_splits} splits")
    print("This respects temporal order (no looking into the future)")

    # Grid search
    print("\nRunning Grid Search...")
    start_time = time.time()

    grid_search = GridSearchCV(
        Ridge(),
        param_grid,
        cv=tscv,
        scoring='neg_mean_absolute_error',
        n_jobs=-1,
        verbose=1
    )

    grid_search.fit(X_train, y_train)

    elapsed = time.time() - start_time
    print(f"\n✓ Grid Search completed in {elapsed:.1f} seconds")

    # Best parameters
    print(f"\nBest parameters:")
    print(f"  alpha: {grid_search.best_params_['alpha']}")
    print(f"\nBest cross-validation MAE: {-grid_search.best_score_:.4f}")

    # Show all results
    print(f"\nAll results:")
    results_df = pd.DataFrame(grid_search.cv_results_)
    for idx, row in results_df.iterrows():
        print(f"  alpha={row['param_alpha']:6.1f} -> MAE={-row['mean_test_score']:.4f} (+/- {row['std_test_score']:.4f})")

    return grid_search.best_estimator_


def tune_xgboost(X_train, y_train):
    """Tune XGBoost hyperparameters."""
    print("\n" + "="*60)
    print("TUNING XGBOOST")
    print("="*60)

    # Parameter grid
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [3, 4, 6],
        'learning_rate': [0.05, 0.1, 0.2],
        'min_child_weight': [1, 3, 5]
    }

    print(f"\nParameter grid:")
    for key, values in param_grid.items():
        print(f"  {key}: {values}")

    total_combinations = np.prod([len(v) for v in param_grid.values()])
    print(f"\nTotal combinations: {total_combinations}")

    # Time-series cross-validation
    tscv = TimeSeriesSplit(n_splits=3)  # Fewer splits for speed

    print(f"\nUsing TimeSeriesSplit with {tscv.n_splits} splits")
    print("This respects temporal order (no looking into the future)")

    # Grid search
    print("\nRunning Grid Search (this will take ~10-15 minutes)...")
    start_time = time.time()

    grid_search = GridSearchCV(
        xgb.XGBRegressor(random_state=42, n_jobs=-1),
        param_grid,
        cv=tscv,
        scoring='neg_mean_absolute_error',
        n_jobs=1,  # XGBoost already uses multiple cores
        verbose=2
    )

    grid_search.fit(X_train, y_train)

    elapsed = time.time() - start_time
    print(f"\n✓ Grid Search completed in {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")

    # Best parameters
    print(f"\nBest parameters:")
    for key, value in grid_search.best_params_.items():
        print(f"  {key}: {value}")
    print(f"\nBest cross-validation MAE: {-grid_search.best_score_:.4f}")

    # Show top 5 results
    print(f"\nTop 5 parameter combinations:")
    results_df = pd.DataFrame(grid_search.cv_results_)
    results_df = results_df.sort_values('rank_test_score')
    for idx, row in results_df.head(5).iterrows():
        print(f"  Rank {int(row['rank_test_score'])}: "
              f"n_est={row['param_n_estimators']}, "
              f"depth={row['param_max_depth']}, "
              f"lr={row['param_learning_rate']}, "
              f"mcw={row['param_min_child_weight']} "
              f"-> MAE={-row['mean_test_score']:.4f}")

    return grid_search.best_estimator_


def evaluate_models(X_train, y_train, X_test, y_test):
    """Train and evaluate default vs tuned models."""

    results = {}

    # Baseline
    last10_pred = X_test['shots_last10_avg'].values
    last10_mae = mean_absolute_error(y_test, last10_pred)
    last10_r2 = r2_score(y_test, last10_pred)
    results['baseline'] = {'mae': last10_mae, 'r2': last10_r2}

    print("\n" + "="*60)
    print("DEFAULT MODELS (Original)")
    print("="*60)

    # Ridge default
    ridge_default = Ridge(alpha=1.0)
    ridge_default.fit(X_train, y_train)

    ridge_default_pred = ridge_default.predict(X_test)
    ridge_default_mae = mean_absolute_error(y_test, ridge_default_pred)
    ridge_default_r2 = r2_score(y_test, ridge_default_pred)

    print(f"\nRidge (alpha=1.0):")
    print(f"  MAE:  {ridge_default_mae:.4f}")
    print(f"  R²:   {ridge_default_r2:.4f}")

    results['ridge_default'] = {'mae': ridge_default_mae, 'r2': ridge_default_r2}

    # XGBoost default
    xgb_default = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        n_jobs=-1
    )
    xgb_default.fit(X_train, y_train, verbose=False)

    xgb_default_pred = xgb_default.predict(X_test)
    xgb_default_mae = mean_absolute_error(y_test, xgb_default_pred)
    xgb_default_r2 = r2_score(y_test, xgb_default_pred)

    print(f"\nXGBoost (default params):")
    print(f"  MAE:  {xgb_default_mae:.4f}")
    print(f"  R²:   {xgb_default_r2:.4f}")

    results['xgb_default'] = {'mae': xgb_default_mae, 'r2': xgb_default_r2}

    # Tune models
    ridge_tuned = tune_ridge(X_train, y_train)
    xgb_tuned = tune_xgboost(X_train, y_train)

    print("\n" + "="*60)
    print("TUNED MODELS (Test Set Performance)")
    print("="*60)

    # Evaluate tuned Ridge
    ridge_tuned_pred = ridge_tuned.predict(X_test)
    ridge_tuned_mae = mean_absolute_error(y_test, ridge_tuned_pred)
    ridge_tuned_r2 = r2_score(y_test, ridge_tuned_pred)

    print(f"\nRidge (tuned):")
    print(f"  MAE:  {ridge_tuned_mae:.4f}")
    print(f"  R²:   {ridge_tuned_r2:.4f}")

    results['ridge_tuned'] = {'mae': ridge_tuned_mae, 'r2': ridge_tuned_r2}

    # Evaluate tuned XGBoost
    xgb_tuned_pred = xgb_tuned.predict(X_test)
    xgb_tuned_mae = mean_absolute_error(y_test, xgb_tuned_pred)
    xgb_tuned_r2 = r2_score(y_test, xgb_tuned_pred)

    print(f"\nXGBoost (tuned):")
    print(f"  MAE:  {xgb_tuned_mae:.4f}")
    print(f"  R²:   {xgb_tuned_r2:.4f}")

    results['xgb_tuned'] = {'mae': xgb_tuned_mae, 'r2': xgb_tuned_r2}

    return results


def compare_results(results):
    """Compare default vs tuned performance."""
    print("\n" + "="*60)
    print("COMPARISON: TUNING IMPACT")
    print("="*60)

    print(f"\n{'Model':<25} {'MAE':>10} {'R²':>10} {'Change':>10}")
    print("-" * 60)

    # Baseline
    print(f"{'Baseline (Last10)':<25} {results['baseline']['mae']:>10.4f} {results['baseline']['r2']:>10.4f} {'-':>10}")

    # Ridge
    ridge_r2_change = results['ridge_tuned']['r2'] - results['ridge_default']['r2']

    print(f"\n{'Ridge (Default)':<25} {results['ridge_default']['mae']:>10.4f} {results['ridge_default']['r2']:>10.4f} {'-':>10}")
    print(f"{'Ridge (Tuned)':<25} {results['ridge_tuned']['mae']:>10.4f} {results['ridge_tuned']['r2']:>10.4f} {ridge_r2_change:>+10.4f}")

    # XGBoost
    xgb_r2_change = results['xgb_tuned']['r2'] - results['xgb_default']['r2']

    print(f"\n{'XGBoost (Default)':<25} {results['xgb_default']['mae']:>10.4f} {results['xgb_default']['r2']:>10.4f} {'-':>10}")
    print(f"{'XGBoost (Tuned)':<25} {results['xgb_tuned']['mae']:>10.4f} {results['xgb_tuned']['r2']:>10.4f} {xgb_r2_change:>+10.4f}")

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    ridge_pct = (ridge_r2_change / results['ridge_default']['r2']) * 100 if results['ridge_default']['r2'] != 0 else 0
    xgb_pct = (xgb_r2_change / results['xgb_default']['r2']) * 100 if results['xgb_default']['r2'] != 0 else 0

    print(f"\nRidge R² change:   {ridge_r2_change:+.4f} ({ridge_pct:+.1f}%)")
    print(f"XGBoost R² change: {xgb_r2_change:+.4f} ({xgb_pct:+.1f}%)")

    if ridge_r2_change > 0 or xgb_r2_change > 0:
        print("\n✓ Hyperparameter tuning IMPROVED performance!")
    else:
        print("\n✗ Hyperparameter tuning did not improve performance")


def main():
    """Main training pipeline."""
    print("="*60)
    print("HYPERPARAMETER TUNING EXPERIMENT")
    print("="*60)
    print("\nThis will take ~10-20 minutes to complete...")

    # Load data
    X_train, y_train, X_test, y_test, feature_cols = load_and_prepare_data()

    # Train and compare
    results = evaluate_models(X_train, y_train, X_test, y_test)

    # Show comparison
    compare_results(results)

    print("\n" + "="*60)
    print("EXPERIMENT COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()