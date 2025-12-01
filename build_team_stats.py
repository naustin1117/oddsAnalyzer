from nhl_api import NHLAPIClient

if __name__ == "__main__":
    with NHLAPIClient() as client:
        # Build team stats from all season's player game logs
        client.build_team_game_stats_from_csvs(
            input_files=[
                'data/player_game_logs_2023_2024.csv',
                'data/player_game_logs_2024_2025.csv',
                'data/player_game_logs_2025_2026.csv'
            ],
            output_file='data/team_game_stats.csv'
        )