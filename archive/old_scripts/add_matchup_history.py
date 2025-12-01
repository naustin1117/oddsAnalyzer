import pandas as pd
import numpy as np


def add_matchup_history(input_file, output_file):
    """
    Add player vs team matchup history features.

    Features added:
    - matchup_shots_avg: Player's average shots against this specific opponent (all-time)
    """
    print(f"Loading {input_file}...")
    df = pd.read_csv(input_file)

    print(f"Initial rows: {len(df)}")

    # Convert game_date to datetime
    df['game_date'] = pd.to_datetime(df['game_date'])

    # Sort by player and game date
    df = df.sort_values(['player_id', 'game_date']).reset_index(drop=True)

    print("\n=== Adding Matchup History Features ===")

    # Initialize new column
    df['matchup_shots_avg'] = 0.0

    # Calculate for each player
    total_players = df['player_id'].nunique()

    for idx, player_id in enumerate(df['player_id'].unique(), 1):
        if idx % 100 == 0:
            print(f"  Processing player {idx}/{total_players}...")

        player_mask = df['player_id'] == player_id
        player_indices = df[player_mask].index.tolist()
        player_data = df.loc[player_indices]

        # For each game this player played
        for i, row_idx in enumerate(player_indices):
            current_opponent = df.loc[row_idx, 'opponent_abbrev']

            # Get all previous games for this player
            prev_indices = player_indices[:i]

            if len(prev_indices) == 0:
                # First game - use player's overall average
                continue

            prev_games = df.loc[prev_indices]

            # Filter to games against current opponent
            matchup_games = prev_games[prev_games['opponent_abbrev'] == current_opponent]

            if len(matchup_games) > 0:
                # Calculate matchup average
                df.loc[row_idx, 'matchup_shots_avg'] = matchup_games['shots'].mean()
            else:
                # First time facing this opponent - use player's overall average
                df.loc[row_idx, 'matchup_shots_avg'] = prev_games['shots'].mean()

    print(f"\n✓ Matchup history feature calculated")

    # Statistics
    print(f"\nFeature statistics:")
    print(f"  matchup_shots_avg:")
    print(f"    Mean: {df['matchup_shots_avg'].mean():.2f}")
    print(f"    Range: {df['matchup_shots_avg'].min():.2f} to {df['matchup_shots_avg'].max():.2f}")

    # Convert game_date back to string for CSV
    df['game_date'] = df['game_date'].dt.strftime('%Y-%m-%d')

    print(f"\nWriting {len(df)} rows to {output_file}...")
    df.to_csv(output_file, index=False)

    print(f"✓ Successfully created {output_file}")


if __name__ == "__main__":
    print("="*60)
    print("ADDING MATCHUP HISTORY FEATURES")
    print("="*60)

    # Process 2023-2024 season
    print("\n" + "="*60)
    print("Processing 2023-2024 Season")
    print("="*60)
    add_matchup_history(
        'data/player_game_logs_2023_2024_with_opponent.csv',
        'data/player_game_logs_2023_2024_with_matchup.csv'
    )

    # Process 2024-2025 season
    print("\n" + "="*60)
    print("Processing 2024-2025 Season")
    print("="*60)
    add_matchup_history(
        'data/player_game_logs_2024_2025_with_opponent.csv',
        'data/player_game_logs_2024_2025_with_matchup.csv'
    )

    print("\n" + "="*60)
    print("MATCHUP HISTORY FEATURES ADDED")
    print("="*60)
    print("\nReady to retrain models with matchup history!")