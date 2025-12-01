import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb


def load_and_prepare_data_by_position():
    """Load training and test data split by position."""
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
    all_train = pd.concat([season_2023_2024, first_half_2024_2025], ignore_index=True)
    all_test = second_half_2024_2025

    # Split by position
    # Forwards: C, L, R
    # Defensemen: D
    train_forwards = all_train[all_train['position_code'].isin(['C', 'L', 'R'])].copy()
    train_defense = all_train[all_train['position_code'] == 'D'].copy()

    test_forwards = all_test[all_test['position_code'].isin(['C', 'L', 'R'])].copy()
    test_defense = all_test[all_test['position_code'] == 'D'].copy()

    print(f"\nTraining data:")
    print(f"  Forwards: {len(train_forwards)} rows")
    print(f"  Defensemen: {len(train_defense)} rows")
    print(f"  Total: {len(all_train)} rows")

    print(f"\nTest data:")
    print(f"  Forwards: {len(test_forwards)} rows")
    print(f"  Defensemen: {len(test_defense)} rows")
    print(f"  Total: {len(all_test)} rows")

    # Define features (exclude target and identifiers)
    exclude_cols = [
        'player_id', 'game_id', 'season_id', 'game_type', 'game_date',
        'team_abbrev', 'opponent_abbrev', 'position_code',
        'shots',  # Target
        'goals', 'assists', 'points', 'plus_minus',
        'power_play_goals', 'power_play_points',
        'shorthanded_goals', 'shorthanded_points',
        'pim', 'shifts', 'toi_raw',
        'toi_minutes'  # Data leakage
    ]

    feature_cols = [col for col in all_train.columns if col not in exclude_cols]
    print(f"\nFeatures ({len(feature_cols)}): {feature_cols}")

    # Prepare datasets
    datasets = {
        'forwards': {
            'X_train': train_forwards[feature_cols],
            'y_train': train_forwards['shots'],
            'X_test': test_forwards[feature_cols],
            'y_test': test_forwards['shots']
        },
        'defense': {
            'X_train': train_defense[feature_cols],
            'y_train': train_defense['shots'],
            'X_test': test_defense[feature_cols],
            'y_test': test_defense['shots']
        }
    }

    # Remove NaN rows
    for position in ['forwards', 'defense']:
        train_mask = ~(datasets[position]['X_train'].isna().any(axis=1) | datasets[position]['y_train'].isna())
        datasets[position]['X_train'] = datasets[position]['X_train'][train_mask]
        datasets[position]['y_train'] = datasets[position]['y_train'][train_mask]

        test_mask = ~(datasets[position]['X_test'].isna().any(axis=1) | datasets[position]['y_test'].isna())
        datasets[position]['X_test'] = datasets[position]['X_test'][test_mask]
        datasets[position]['y_test'] = datasets[position]['y_test'][test_mask]

    print(f"\nAfter removing NaN:")
    for position in ['forwards', 'defense']:
        print(f"  {position.capitalize()}:")
        print(f"    Train: {len(datasets[position]['X_train'])} rows")
        print(f"    Test: {len(datasets[position]['X_test'])} rows")

    return datasets, feature_cols


def train_position_model(position, X_train, y_train, X_test, y_test):
    """Train Ridge and XGBoost models for a specific position."""
    print("\n" + "="*60)
    print(f"{position.upper()} MODELS")
    print("="*60)

    results = {}

    # Baseline: shots_last10_avg
    last10_pred = X_test['shots_last10_avg'].values
    last10_mae = mean_absolute_error(y_test, last10_pred)
    last10_rmse = np.sqrt(mean_squared_error(y_test, last10_pred))
    last10_r2 = r2_score(y_test, last10_pred)

    print(f"\nBaseline (Last10 Avg):")
    print(f"  MAE:  {last10_mae:.4f}")
    print(f"  RMSE: {last10_rmse:.4f}")
    print(f"  R²:   {last10_r2:.4f}")

    results['baseline'] = {'mae': last10_mae, 'rmse': last10_rmse, 'r2': last10_r2}

    # Ridge Regression
    ridge = Ridge(alpha=1.0)
    ridge.fit(X_train, y_train)

    ridge_pred = ridge.predict(X_test)
    ridge_mae = mean_absolute_error(y_test, ridge_pred)
    ridge_rmse = np.sqrt(mean_squared_error(y_test, ridge_pred))
    ridge_r2 = r2_score(y_test, ridge_pred)

    print(f"\nRidge Regression:")
    print(f"  MAE:  {ridge_mae:.4f}")
    print(f"  RMSE: {ridge_rmse:.4f}")
    print(f"  R²:   {ridge_r2:.4f}")

    results['ridge'] = {'mae': ridge_mae, 'rmse': ridge_rmse, 'r2': ridge_r2}

    # XGBoost
    xgb_model = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        n_jobs=-1
    )
    xgb_model.fit(X_train, y_train, verbose=False)

    xgb_pred = xgb_model.predict(X_test)
    xgb_mae = mean_absolute_error(y_test, xgb_pred)
    xgb_rmse = np.sqrt(mean_squared_error(y_test, xgb_pred))
    xgb_r2 = r2_score(y_test, xgb_pred)

    print(f"\nXGBoost:")
    print(f"  MAE:  {xgb_mae:.4f}")
    print(f"  RMSE: {xgb_rmse:.4f}")
    print(f"  R²:   {xgb_r2:.4f}")

    results['xgboost'] = {'mae': xgb_mae, 'rmse': xgb_rmse, 'r2': xgb_r2}

    return results


def main():
    """Main training pipeline."""
    print("="*60)
    print("POSITION-SPECIFIC MODEL TRAINING")
    print("="*60)

    # Load data split by position
    datasets, feature_cols = load_and_prepare_data_by_position()

    # Train models for each position
    all_results = {}

    for position in ['forwards', 'defense']:
        results = train_position_model(
            position,
            datasets[position]['X_train'],
            datasets[position]['y_train'],
            datasets[position]['X_test'],
            datasets[position]['y_test']
        )
        all_results[position] = results

    # Summary comparison
    print("\n" + "="*60)
    print("SUMMARY COMPARISON")
    print("="*60)

    for position in ['forwards', 'defense']:
        print(f"\n{position.upper()}:")
        print(f"  Baseline Last10: R²={all_results[position]['baseline']['r2']:.4f}, MAE={all_results[position]['baseline']['mae']:.4f}")
        print(f"  Ridge:           R²={all_results[position]['ridge']['r2']:.4f}, MAE={all_results[position]['ridge']['mae']:.4f}")
        print(f"  XGBoost:         R²={all_results[position]['xgboost']['r2']:.4f}, MAE={all_results[position]['xgboost']['mae']:.4f}")

    # Calculate weighted average across positions
    fwd_count = len(datasets['forwards']['y_test'])
    def_count = len(datasets['defense']['y_test'])
    total_count = fwd_count + def_count

    print(f"\nWEIGHTED AVERAGE (across {total_count} test samples):")
    for model in ['baseline', 'ridge', 'xgboost']:
        weighted_r2 = (all_results['forwards'][model]['r2'] * fwd_count +
                       all_results['defense'][model]['r2'] * def_count) / total_count
        weighted_mae = (all_results['forwards'][model]['mae'] * fwd_count +
                        all_results['defense'][model]['mae'] * def_count) / total_count

        model_name = model.capitalize() if model != 'xgboost' else 'XGBoost'
        if model == 'baseline':
            model_name = 'Baseline Last10'

        print(f"  {model_name:20s}: R²={weighted_r2:.4f}, MAE={weighted_mae:.4f}")

    print("\n" + "="*60)
    print("TRAINING COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()