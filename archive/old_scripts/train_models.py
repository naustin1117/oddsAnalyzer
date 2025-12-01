import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
import matplotlib.pyplot as plt


def load_and_prepare_data():
    """Load training and test data."""
    print("Loading data...")

    # Load both seasons (with opponent features)
    season_2023_2024 = pd.read_csv('data/player_game_logs_2023_2024_with_opponent.csv')
    season_2024_2025 = pd.read_csv('data/player_game_logs_2024_2025_with_opponent.csv')

    print(f"2023-2024 season: {len(season_2023_2024)} rows")
    print(f"2024-2025 season: {len(season_2024_2025)} rows")

    # Sort 2024-2025 by date and split in half
    season_2024_2025['game_date'] = pd.to_datetime(season_2024_2025['game_date'])
    season_2024_2025 = season_2024_2025.sort_values('game_date').reset_index(drop=True)

    # Find midpoint by date
    midpoint_idx = len(season_2024_2025) // 2
    midpoint_date = season_2024_2025.loc[midpoint_idx, 'game_date']

    # Split into first half (train) and second half (test)
    first_half_2024_2025 = season_2024_2025[season_2024_2025['game_date'] < midpoint_date].copy()
    second_half_2024_2025 = season_2024_2025[season_2024_2025['game_date'] >= midpoint_date].copy()

    print(f"\n2024-2025 split at: {midpoint_date.strftime('%Y-%m-%d')}")
    print(f"  First half (train): {len(first_half_2024_2025)} rows")
    print(f"  Second half (test): {len(second_half_2024_2025)} rows")

    # Combine 2023-2024 + first half of 2024-2025 as training data
    train_df = pd.concat([season_2023_2024, first_half_2024_2025], ignore_index=True)
    test_df = second_half_2024_2025

    print(f"\nFinal split:")
    print(f"  Train set: {len(train_df)} rows (2023-2024 + first half 2024-2025)")
    print(f"  Test set: {len(test_df)} rows (second half 2024-2025)")

    # Define features (exclude target and identifiers)
    exclude_cols = [
        'player_id', 'game_id', 'season_id', 'game_type', 'game_date',
        'team_abbrev', 'opponent_abbrev', 'position_code',
        'shots',  # This is our target
        'goals', 'assists', 'points', 'plus_minus',  # Other outcomes
        'power_play_goals', 'power_play_points',
        'shorthanded_goals', 'shorthanded_points',
        'pim', 'shifts', 'toi_raw',
        'toi_minutes'  # Data leakage - we don't know TOI before the game
    ]
    # Note: home_flag, days_since_last_game, and opponent_shots_allowed_avg are now INCLUDED
    # Historical TOI features (toi_last5_sum, toi_last10_sum, toi_season_to_date) are still included

    feature_cols = [col for col in train_df.columns if col not in exclude_cols]

    print(f"\nFeatures ({len(feature_cols)}): {feature_cols}")

    # Prepare train and test sets
    X_train = train_df[feature_cols]
    y_train = train_df['shots']

    X_test = test_df[feature_cols]
    y_test = test_df['shots']

    # Remove any rows with NaN
    train_mask = ~(X_train.isna().any(axis=1) | y_train.isna())
    X_train = X_train[train_mask]
    y_train = y_train[train_mask]

    test_mask = ~(X_test.isna().any(axis=1) | y_test.isna())
    X_test = X_test[test_mask]
    y_test = y_test[test_mask]

    print(f"\nAfter removing NaN:")
    print(f"Train set: {len(X_train)} rows")
    print(f"Test set: {len(X_test)} rows")

    return X_train, y_train, X_test, y_test, feature_cols


def train_baseline_models(X_train, y_train, X_test, y_test):
    """Train simple baseline models."""
    print("\n" + "="*60)
    print("BASELINE MODELS")
    print("="*60)

    # Baseline 1: Predict mean of training data
    mean_pred = np.full(len(y_test), y_train.mean())
    mean_mae = mean_absolute_error(y_test, mean_pred)
    mean_rmse = np.sqrt(mean_squared_error(y_test, mean_pred))
    mean_r2 = r2_score(y_test, mean_pred)

    print("\nBaseline 1: Always predict training mean ({:.2f} shots)".format(y_train.mean()))
    print(f"  MAE:  {mean_mae:.4f}")
    print(f"  RMSE: {mean_rmse:.4f}")
    print(f"  R²:   {mean_r2:.4f}")

    # Baseline 2: Use shots_last10_avg directly
    last10_pred = X_test['shots_last10_avg'].values
    last10_mae = mean_absolute_error(y_test, last10_pred)
    last10_rmse = np.sqrt(mean_squared_error(y_test, last10_pred))
    last10_r2 = r2_score(y_test, last10_pred)

    print("\nBaseline 2: Use shots_last10_avg as prediction")
    print(f"  MAE:  {last10_mae:.4f}")
    print(f"  RMSE: {last10_rmse:.4f}")
    print(f"  R²:   {last10_r2:.4f}")

    # Baseline 3: Use shots_last5_avg directly
    last5_pred = X_test['shots_last5_avg'].values
    last5_mae = mean_absolute_error(y_test, last5_pred)
    last5_rmse = np.sqrt(mean_squared_error(y_test, last5_pred))
    last5_r2 = r2_score(y_test, last5_pred)

    print("\nBaseline 3: Use shots_last5_avg as prediction")
    print(f"  MAE:  {last5_mae:.4f}")
    print(f"  RMSE: {last5_rmse:.4f}")
    print(f"  R²:   {last5_r2:.4f}")

    return {
        'mean': (mean_mae, mean_rmse, mean_r2),
        'last10': (last10_mae, last10_rmse, last10_r2),
        'last5': (last5_mae, last5_rmse, last5_r2)
    }


def train_ridge_model(X_train, y_train, X_test, y_test):
    """Train Ridge Regression model."""
    print("\n" + "="*60)
    print("RIDGE REGRESSION")
    print("="*60)

    # Train model
    model = Ridge(alpha=1.0)
    model.fit(X_train, y_train)

    # Make predictions
    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)

    # Evaluate
    train_mae = mean_absolute_error(y_train, train_pred)
    train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
    train_r2 = r2_score(y_train, train_pred)

    test_mae = mean_absolute_error(y_test, test_pred)
    test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
    test_r2 = r2_score(y_test, test_pred)

    print("\nTraining Set Performance:")
    print(f"  MAE:  {train_mae:.4f}")
    print(f"  RMSE: {train_rmse:.4f}")
    print(f"  R²:   {train_r2:.4f}")

    print("\nTest Set Performance:")
    print(f"  MAE:  {test_mae:.4f}")
    print(f"  RMSE: {test_rmse:.4f}")
    print(f"  R²:   {test_r2:.4f}")

    return model, test_pred, test_mae, test_rmse, test_r2


def train_xgboost_model(X_train, y_train, X_test, y_test):
    """Train XGBoost model."""
    print("\n" + "="*60)
    print("XGBOOST")
    print("="*60)

    # Train model
    model = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train, verbose=False)

    # Make predictions
    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)

    # Evaluate
    train_mae = mean_absolute_error(y_train, train_pred)
    train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
    train_r2 = r2_score(y_train, train_pred)

    test_mae = mean_absolute_error(y_test, test_pred)
    test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
    test_r2 = r2_score(y_test, test_pred)

    print("\nTraining Set Performance:")
    print(f"  MAE:  {train_mae:.4f}")
    print(f"  RMSE: {train_rmse:.4f}")
    print(f"  R²:   {train_r2:.4f}")

    print("\nTest Set Performance:")
    print(f"  MAE:  {test_mae:.4f}")
    print(f"  RMSE: {test_rmse:.4f}")
    print(f"  R²:   {test_r2:.4f}")

    return model, test_pred, test_mae, test_rmse, test_r2


def show_feature_importance(ridge_model, xgb_model, feature_cols):
    """Display feature importance for both models."""
    print("\n" + "="*60)
    print("FEATURE IMPORTANCE")
    print("="*60)

    # Ridge coefficients
    ridge_importance = pd.DataFrame({
        'feature': feature_cols,
        'coefficient': np.abs(ridge_model.coef_)
    }).sort_values('coefficient', ascending=False)

    print("\nTop 10 Features (Ridge - Absolute Coefficients):")
    for i, row in ridge_importance.head(10).iterrows():
        print(f"  {row['feature']:30s}: {row['coefficient']:.4f}")

    # XGBoost feature importance
    xgb_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': xgb_model.feature_importances_
    }).sort_values('importance', ascending=False)

    print("\nTop 10 Features (XGBoost - Gain):")
    for i, row in xgb_importance.head(10).iterrows():
        print(f"  {row['feature']:30s}: {row['importance']:.4f}")


def compare_models(baseline_metrics, ridge_metrics, xgb_metrics):
    """Compare model performance."""
    print("\n" + "="*60)
    print("MODEL COMPARISON (Test Set)")
    print("="*60)

    # Extract metrics
    mean_mae, mean_rmse, mean_r2 = baseline_metrics['mean']
    last10_mae, last10_rmse, last10_r2 = baseline_metrics['last10']
    last5_mae, last5_rmse, last5_r2 = baseline_metrics['last5']
    ridge_mae, ridge_rmse, ridge_r2 = ridge_metrics
    xgb_mae, xgb_rmse, xgb_r2 = xgb_metrics

    print(f"\n{'Model':<20} {'MAE':>10} {'RMSE':>10} {'R²':>10}")
    print("-" * 52)
    print(f"{'Mean Baseline':<20} {mean_mae:>10.4f} {mean_rmse:>10.4f} {mean_r2:>10.4f}")
    print(f"{'Last5 Avg':<20} {last5_mae:>10.4f} {last5_rmse:>10.4f} {last5_r2:>10.4f}")
    print(f"{'Last10 Avg':<20} {last10_mae:>10.4f} {last10_rmse:>10.4f} {last10_r2:>10.4f}")
    print(f"{'Ridge':<20} {ridge_mae:>10.4f} {ridge_rmse:>10.4f} {ridge_r2:>10.4f}")
    print(f"{'XGBoost':<20} {xgb_mae:>10.4f} {xgb_rmse:>10.4f} {xgb_r2:>10.4f}")

    # Find best for each metric
    all_maes = [mean_mae, last5_mae, last10_mae, ridge_mae, xgb_mae]
    all_rmses = [mean_rmse, last5_rmse, last10_rmse, ridge_rmse, xgb_rmse]
    all_r2s = [mean_r2, last5_r2, last10_r2, ridge_r2, xgb_r2]
    models = ['Mean', 'Last5', 'Last10', 'Ridge', 'XGBoost']

    print("\n" + "="*52)
    print("WINNERS")
    print("="*52)
    print(f"Best MAE:  {models[all_maes.index(min(all_maes))]} ({min(all_maes):.4f})")
    print(f"Best RMSE: {models[all_rmses.index(min(all_rmses))]} ({min(all_rmses):.4f})")
    print(f"Best R²:   {models[all_r2s.index(max(all_r2s))]} ({max(all_r2s):.4f})")


def main():
    """Main training pipeline."""
    print("="*60)
    print("NHL SHOTS ON GOAL PREDICTION")
    print("="*60)

    # Load data
    X_train, y_train, X_test, y_test, feature_cols = load_and_prepare_data()

    # Train baseline models
    baseline_metrics = train_baseline_models(X_train, y_train, X_test, y_test)

    # Train Ridge
    ridge_model, ridge_pred, ridge_mae, ridge_rmse, ridge_r2 = train_ridge_model(
        X_train, y_train, X_test, y_test
    )

    # Train XGBoost
    xgb_model, xgb_pred, xgb_mae, xgb_rmse, xgb_r2 = train_xgboost_model(
        X_train, y_train, X_test, y_test
    )

    # Show feature importance
    show_feature_importance(ridge_model, xgb_model, feature_cols)

    # Compare models
    compare_models(
        baseline_metrics,
        (ridge_mae, ridge_rmse, ridge_r2),
        (xgb_mae, xgb_rmse, xgb_r2)
    )

    print("\n" + "="*60)
    print("TRAINING COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()