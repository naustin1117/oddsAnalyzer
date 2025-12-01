import pandas as pd
from nhl_api import NHLAPIClient


def create_player_position_mapping(seasons, output_file='data/player_positions.csv'):
    """
    Create a mapping of player_id to position_code from skater stats.

    Args:
        seasons: List of season IDs (e.g., ['20232024', '20242025'])
        output_file: Output CSV file path
    """
    print("="*60)
    print("CREATING PLAYER POSITION MAPPING")
    print("="*60)

    all_players = []

    with NHLAPIClient() as client:
        for season in seasons:
            print(f"\nFetching player positions for {season}...")
            stats = client.get_all_skater_stats(season, game_type=2, limit=-1)

            if stats and 'data' in stats:
                for player in stats['data']:
                    all_players.append({
                        'player_id': player.get('playerId'),
                        'position_code': player.get('positionCode'),
                        'player_name': player.get('skaterFullName')
                    })
                print(f"  Found {len(stats['data'])} players")

    # Create DataFrame and remove duplicates (keep first occurrence)
    df = pd.DataFrame(all_players)
    df = df.drop_duplicates(subset=['player_id'], keep='first')

    print(f"\nTotal unique players: {len(df)}")
    print(f"Position breakdown:")
    print(df['position_code'].value_counts())

    # Save to CSV
    df.to_csv(output_file, index=False)
    print(f"\n✓ Successfully created {output_file}")

    return df


def add_positions_to_game_logs(game_log_files, position_file='data/player_positions.csv'):
    """
    Add position_code to game log files.

    Args:
        game_log_files: List of game log CSV files to update
        position_file: Player position mapping CSV
    """
    print("\n" + "="*60)
    print("ADDING POSITIONS TO GAME LOGS")
    print("="*60)

    # Load position mapping
    print(f"\nLoading {position_file}...")
    positions = pd.read_csv(position_file)

    for file in game_log_files:
        print(f"\nProcessing {file}...")
        df = pd.read_csv(file)

        # Drop existing position_code if it exists
        if 'position_code' in df.columns:
            df = df.drop('position_code', axis=1)

        # Merge position data
        df = df.merge(positions[['player_id', 'position_code']], on='player_id', how='left')

        # Check for missing positions
        missing = df['position_code'].isna().sum()
        if missing > 0:
            print(f"  Warning: {missing} rows have missing position data")

        print(f"  Position breakdown:")
        print(f"    {df['position_code'].value_counts().to_dict()}")

        # Save updated file
        df.to_csv(file, index=False)
        print(f"  ✓ Updated {file}")

    print("\n" + "="*60)
    print("ALL POSITIONS ADDED")
    print("="*60)


if __name__ == "__main__":
    # Create position mapping from both seasons
    positions = create_player_position_mapping(
        seasons=['20232024', '20242025'],
        output_file='data/player_positions.csv'
    )

    # Add positions to all game log files
    add_positions_to_game_logs([
        'data/player_game_logs_2023_2024_with_opponent.csv',
        'data/player_game_logs_2024_2025_with_opponent.csv'
    ])