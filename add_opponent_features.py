import pandas as pd
import numpy as np


def add_opponent_features(input_file, output_file, team_stats_file='data/team_game_stats.csv'):
    """
    Add opponent and context features to the engineered data.

    Features added:
    - days_since_last_game: Days of rest
    - opponent_shots_allowed_avg: Opponent's average shots allowed season-to-date
    - opponent_shots_allowed_last5: Opponent's shots allowed average over last 5 games
    - opponent_shots_allowed_last10: Opponent's shots allowed average over last 10 games
    - home_flag: Already exists, just noting it should be included in features
    """
    print(f"Loading {input_file}...")
    df = pd.read_csv(input_file)

    print(f"Initial rows: {len(df)}")

    # Convert game_date to datetime
    df['game_date'] = pd.to_datetime(df['game_date'])

    # Sort by player and game date
    df = df.sort_values(['player_id', 'game_date']).reset_index(drop=True)

    print("\n=== Adding Feature 1: Days Since Last Game ===")

    # Calculate days since last game for each player
    df['days_since_last_game'] = 0.0

    for player_id in df['player_id'].unique():
        player_mask = df['player_id'] == player_id
        player_indices = df[player_mask].index.tolist()

        for i in range(1, len(player_indices)):
            idx = player_indices[i]
            prev_idx = player_indices[i-1]

            days_diff = (df.loc[idx, 'game_date'] - df.loc[prev_idx, 'game_date']).days
            df.loc[idx, 'days_since_last_game'] = days_diff

    print(f"  Added days_since_last_game")
    print(f"  Range: {df['days_since_last_game'].min():.0f} to {df['days_since_last_game'].max():.0f} days")
    print(f"  Average: {df['days_since_last_game'].mean():.1f} days")

    print("\n=== Adding Opponent Defensive Features ===")

    # Load team game stats
    print(f"Loading {team_stats_file}...")
    team_stats = pd.read_csv(team_stats_file)
    team_stats['game_date'] = pd.to_datetime(team_stats['game_date'])

    # Sort by team and date
    team_stats = team_stats.sort_values(['team_abbrev', 'game_date']).reset_index(drop=True)

    # Calculate rolling averages for each team
    team_stats['opponent_shots_allowed_avg'] = 0.0
    team_stats['opponent_shots_allowed_last5'] = 0.0
    team_stats['opponent_shots_allowed_last10'] = 0.0

    for team in team_stats['team_abbrev'].unique():
        team_mask = team_stats['team_abbrev'] == team
        team_indices = team_stats[team_mask].index.tolist()

        for i, idx in enumerate(team_indices):
            # Previous games for this team
            prev_indices = team_indices[:i]

            if len(prev_indices) == 0:
                # First game - use overall average as placeholder
                continue

            prev_games = team_stats.loc[prev_indices]

            # Season-to-date average
            team_stats.loc[idx, 'opponent_shots_allowed_avg'] = prev_games['shots_against'].mean()

            # Last 5 games average
            last5_games = prev_games.tail(5)
            team_stats.loc[idx, 'opponent_shots_allowed_last5'] = last5_games['shots_against'].mean()

            # Last 10 games average
            last10_games = prev_games.tail(10)
            team_stats.loc[idx, 'opponent_shots_allowed_last10'] = last10_games['shots_against'].mean()

    # Fill first game values with overall averages
    overall_avg = team_stats['shots_against'].mean()
    team_stats['opponent_shots_allowed_avg'] = team_stats['opponent_shots_allowed_avg'].replace(0, overall_avg)
    team_stats['opponent_shots_allowed_last5'] = team_stats['opponent_shots_allowed_last5'].replace(0, overall_avg)
    team_stats['opponent_shots_allowed_last10'] = team_stats['opponent_shots_allowed_last10'].replace(0, overall_avg)

    print(f"  Calculated opponent defensive metrics for {team_stats['team_abbrev'].nunique()} teams")

    # Merge with player game logs
    print(f"  Merging opponent features into player game logs...")
    df = df.merge(
        team_stats[['game_date', 'team_abbrev', 'opponent_shots_allowed_avg',
                    'opponent_shots_allowed_last5', 'opponent_shots_allowed_last10']],
        left_on=['game_date', 'opponent_abbrev'],
        right_on=['game_date', 'team_abbrev'],
        how='left',
        suffixes=('', '_team')
    )

    # Drop the redundant team_abbrev_team column
    df = df.drop('team_abbrev_team', axis=1)

    # Fill any remaining NaN with overall average
    df['opponent_shots_allowed_avg'] = df['opponent_shots_allowed_avg'].fillna(overall_avg)
    df['opponent_shots_allowed_last5'] = df['opponent_shots_allowed_last5'].fillna(overall_avg)
    df['opponent_shots_allowed_last10'] = df['opponent_shots_allowed_last10'].fillna(overall_avg)

    print(f"  Added opponent_shots_allowed_avg")
    print(f"    Range: {df['opponent_shots_allowed_avg'].min():.1f} to {df['opponent_shots_allowed_avg'].max():.1f} shots")
    print(f"    Average: {df['opponent_shots_allowed_avg'].mean():.1f} shots per game")

    print(f"  Added opponent_shots_allowed_last5")
    print(f"    Range: {df['opponent_shots_allowed_last5'].min():.1f} to {df['opponent_shots_allowed_last5'].max():.1f} shots")
    print(f"    Average: {df['opponent_shots_allowed_last5'].mean():.1f} shots per game")

    print(f"  Added opponent_shots_allowed_last10")
    print(f"    Range: {df['opponent_shots_allowed_last10'].min():.1f} to {df['opponent_shots_allowed_last10'].max():.1f} shots")
    print(f"    Average: {df['opponent_shots_allowed_last10'].mean():.1f} shots per game")

    print(f"\n=== Summary ===")
    print(f"New features added:")
    print(f"  1. days_since_last_game")
    print(f"  2. opponent_shots_allowed_avg (season-to-date)")
    print(f"  3. opponent_shots_allowed_last5 (last 5 games)")
    print(f"  4. opponent_shots_allowed_last10 (last 10 games)")
    print(f"  5. home_flag (already exists, will be included in training)")

    # Convert game_date back to string for CSV
    df['game_date'] = df['game_date'].dt.strftime('%Y-%m-%d')

    print(f"\nWriting {len(df)} rows to {output_file}...")
    df.to_csv(output_file, index=False)

    print(f"✓ Successfully created {output_file}")


if __name__ == "__main__":
    print("="*60)
    print("ADDING OPPONENT AND CONTEXT FEATURES")
    print("="*60)

    # Process 2023-2024 season
    print("\n" + "="*60)
    print("Processing 2023-2024 Season")
    print("="*60)
    add_opponent_features(
        'data/player_game_logs_2023_2024_engineered.csv',
        'data/player_game_logs_2023_2024_with_opponent.csv'
    )

    # Process 2024-2025 season
    print("\n" + "="*60)
    print("Processing 2024-2025 Season")
    print("="*60)
    add_opponent_features(
        'data/player_game_logs_2024_2025_engineered.csv',
        'data/player_game_logs_2024_2025_with_opponent.csv'
    )

    print("\n" + "="*60)
    print("ALL FEATURES ADDED")
    print("="*60)
    print("\nReady to retrain models with new features!")