import requests
import csv
import pandas as pd
from typing import Optional, Dict, Any, List


class NHLAPIClient:
    """Client for interacting with the NHL API."""

    BASE_URL = "https://api-web.nhle.com/v1"
    STATS_BASE_URL = "https://api.nhle.com/stats/rest/en"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })

    def get_player_game_log(
        self,
        player_id: int,
        season_id: str,
        game_type: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get game log for a specific player.

        Args:
            player_id: NHL player ID (e.g., 8478402)
            season_id: Season in format YYYYYYYY (e.g., "20232024")
            game_type: Game type (2 = regular season, 3 = playoffs)

        Returns:
            JSON response from the API or None if request fails
        """
        endpoint = f"{self.BASE_URL}/player/{player_id}/game-log/{season_id}/{game_type}"

        try:
            response = self.session.get(endpoint, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching player game log: {e}")
            return None

    def get_all_skater_stats(
        self,
        season_id: str,
        game_type: int,
        limit: int = -1
    ) -> Optional[Dict[str, Any]]:
        """
        Get realtime stats for all skaters in a given season.

        Args:
            season_id: Season in format YYYYYYYY (e.g., "20232024")
            game_type: Game type (2 = regular season, 3 = playoffs)
            limit: Number of results to return (-1 for all players, default: -1)

        Returns:
            JSON response from the API containing player stats or None if request fails
        """
        endpoint = f"{self.STATS_BASE_URL}/skater/realtime"
        params = {
            "limit": limit,
            "cayenneExp": f"seasonId={season_id} and gameTypeId={game_type}"
        }

        try:
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching skater stats: {e}")
            return None

    def get_schedule(self, date: str) -> Optional[Dict[str, Any]]:
        """
        Get the NHL schedule for a specific date.

        Args:
            date: Date in format YYYY-MM-DD (e.g., "2023-11-10")

        Returns:
            JSON response from the API containing the schedule or None if request fails
        """
        endpoint = f"{self.BASE_URL}/schedule/{date}"

        try:
            response = self.session.get(endpoint, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching schedule: {e}")
            return None

    def get_team_week_schedule(
        self,
        team_code: str,
        date: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a team's schedule for the week containing the specified date.

        Args:
            team_code: Team abbreviation (e.g., "EDM", "TOR", "MTL")
            date: Date in format YYYY-MM-DD (e.g., "2023-11-10")

        Returns:
            JSON response from the API containing the team's weekly schedule or None if request fails
        """
        endpoint = f"{self.BASE_URL}/club-schedule/{team_code}/week/{date}"

        try:
            response = self.session.get(endpoint, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching team week schedule: {e}")
            return None

    def get_boxscore(self, game_id: int) -> Optional[Dict[str, Any]]:
        """
        Get boxscore data for a specific game.

        Args:
            game_id: NHL game ID (e.g., 2024020019)

        Returns:
            JSON response from the API containing boxscore data or None if request fails
        """
        endpoint = f"{self.BASE_URL}/gamecenter/{game_id}/boxscore"

        try:
            response = self.session.get(endpoint, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching boxscore for game {game_id}: {e}")
            return None

    def export_all_player_game_logs_to_csv(
        self,
        season_id: str,
        game_type: int,
        output_file: str = "player_game_logs.csv"
    ) -> None:
        """
        Export all player game logs for a season to a CSV file.

        Args:
            season_id: Season in format YYYYYYYY (e.g., "20232024")
            game_type: Game type (2 = regular season, 3 = playoffs)
            output_file: Output CSV file path (default: "player_game_logs.csv")
        """
        print(f"Fetching all skater stats for season {season_id}...")
        skater_stats = self.get_all_skater_stats(season_id, game_type)

        if not skater_stats or 'data' not in skater_stats:
            print("Failed to fetch skater stats")
            return

        players = skater_stats['data']
        player_ids = list(set([player['playerId'] for player in players]))
        print(f"Found {len(player_ids)} unique players")

        # CSV headers
        headers = [
            'player_id', 'game_id', 'season_id', 'game_type', 'game_date',
            'team_abbrev', 'opponent_abbrev', 'home_flag', 'position_code',
            'shots', 'goals', 'assists', 'points', 'plus_minus',
            'power_play_goals', 'power_play_points', 'shorthanded_goals',
            'shorthanded_points', 'pim', 'shifts', 'toi_raw'
        ]

        all_rows = []
        total_players = len(player_ids)

        for idx, player_id in enumerate(player_ids, 1):
            print(f"Processing player {idx}/{total_players} (ID: {player_id})...")

            game_log = self.get_player_game_log(player_id, season_id, game_type)

            if not game_log or 'gameLog' not in game_log:
                print(f"  No game log data for player {player_id}")
                continue

            games = game_log['gameLog']
            print(f"  Found {len(games)} games")

            for game in games:
                row = {
                    'player_id': player_id,
                    'game_id': game.get('gameId'),
                    'season_id': season_id,
                    'game_type': game_type,
                    'game_date': game.get('gameDate'),
                    'team_abbrev': game.get('teamAbbrev'),
                    'opponent_abbrev': game.get('opponentAbbrev'),
                    'home_flag': 1 if game.get('homeRoadFlag') == 'H' else 0,
                    'position_code': game.get('positionCode'),
                    'shots': game.get('shots'),
                    'goals': game.get('goals'),
                    'assists': game.get('assists'),
                    'points': game.get('points'),
                    'plus_minus': game.get('plusMinus'),
                    'power_play_goals': game.get('powerPlayGoals'),
                    'power_play_points': game.get('powerPlayPoints'),
                    'shorthanded_goals': game.get('shorthandedGoals'),
                    'shorthanded_points': game.get('shorthandedPoints'),
                    'pim': game.get('pim'),
                    'shifts': game.get('shifts'),
                    'toi_raw': game.get('toi')
                }
                all_rows.append(row)

        print(f"\nWriting {len(all_rows)} game records to {output_file}...")
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(all_rows)

        print(f"✓ Successfully exported data to {output_file}")

    def update_player_game_logs_incremental(
        self,
        date: str,
        season_id: str,
        game_type: int,
        csv_file: str = "data/player_game_logs_2025_2026.csv"
    ) -> None:
        """
        Incrementally update player game logs by fetching only games from a specific date.
        Uses schedule API to get game IDs, then fetches boxscores for player stats.

        Args:
            date: Date in format YYYY-MM-DD (e.g., "2024-12-01")
            season_id: Season in format YYYYYYYY (e.g., "20252026")
            game_type: Game type (2 = regular season, 3 = playoffs)
            csv_file: Path to CSV file to update
        """
        print(f"Fetching games for {date}...")
        schedule = self.get_schedule(date)

        if not schedule or 'gameWeek' not in schedule:
            print(f"No games found for {date}")
            return

        # Extract game IDs from schedule
        game_ids = []
        for day in schedule.get('gameWeek', []):
            for game in day.get('games', []):
                game_id = game.get('id')
                if game_id:
                    game_ids.append(game_id)

        if not game_ids:
            print(f"No games found for {date}")
            return

        print(f"Found {len(game_ids)} games to process")

        # Load existing data
        try:
            df_existing = pd.read_csv(csv_file)
            existing_game_ids = set(df_existing['game_id'].unique())
            print(f"Loaded {len(existing_game_ids)} existing games from {csv_file}")
        except FileNotFoundError:
            print(f"{csv_file} not found - will create new file")
            df_existing = pd.DataFrame()
            existing_game_ids = set()

        new_rows = []

        for idx, game_id in enumerate(game_ids, 1):
            if game_id in existing_game_ids:
                print(f"  Game {idx}/{len(game_ids)} (ID: {game_id}) - Already in CSV, skipping")
                continue

            print(f"  Game {idx}/{len(game_ids)} (ID: {game_id}) - Fetching boxscore...")
            boxscore = self.get_boxscore(game_id)

            if not boxscore:
                print(f"    Failed to fetch boxscore")
                continue

            # Extract player stats from boxscore
            player_stats = boxscore.get('playerByGameStats', {})

            for team_key in ['awayTeam', 'homeTeam']:
                team_data = player_stats.get(team_key, {})
                is_home = (team_key == 'homeTeam')

                team_abbrev = boxscore.get('awayTeam' if team_key == 'awayTeam' else 'homeTeam', {}).get('abbrev', '')
                opponent_abbrev = boxscore.get('homeTeam' if team_key == 'awayTeam' else 'awayTeam', {}).get('abbrev', '')

                for position in ['forwards', 'defense']:
                    for player in team_data.get(position, []):
                        row = {
                            'player_id': player.get('playerId'),
                            'game_id': game_id,
                            'season_id': season_id,
                            'game_type': game_type,
                            'game_date': date,
                            'team_abbrev': team_abbrev,
                            'opponent_abbrev': opponent_abbrev,
                            'home_flag': 1 if is_home else 0,
                            'position_code': player.get('position', 'D' if position == 'defense' else 'F'),
                            'shots': player.get('sog', 0),
                            'goals': player.get('goals', 0),
                            'assists': player.get('assists', 0),
                            'points': player.get('points', 0),
                            'plus_minus': player.get('plusMinus', 0),
                            'power_play_goals': player.get('powerPlayGoals', 0),
                            'power_play_points': 0,
                            'shorthanded_goals': player.get('shorthandedGoals', 0),
                            'shorthanded_points': 0,
                            'pim': player.get('pim', 0),
                            'shifts': player.get('shifts', 0),
                            'toi_raw': player.get('toi', '0:00')
                        }
                        new_rows.append(row)

            print(f"    Added {len([r for r in new_rows if r['game_id'] == game_id])} player records")

        if not new_rows:
            print(f"\n✓ No new games to add - {csv_file} is up to date")
            return

        # Append new rows
        print(f"\nAppending {len(new_rows)} new player-game records to {csv_file}...")
        new_df = pd.DataFrame(new_rows)

        if len(df_existing) > 0:
            combined_df = pd.concat([df_existing, new_df], ignore_index=True)
        else:
            combined_df = new_df

        combined_df.to_csv(csv_file, index=False)
        print(f"✓ Successfully updated {csv_file}")
        print(f"  Total records: {len(combined_df)} ({len(new_rows)} new)")

    @staticmethod
    def clean_toi_column(input_file: str, output_file: str = None) -> None:
        """
        Clean the toi_raw column by removing trailing :00 from MM:SS:00 format.

        Args:
            input_file: Input CSV file path
            output_file: Output CSV file path (if None, overwrites input file)
        """
        import re

        if output_file is None:
            output_file = input_file

        print(f"Reading {input_file}...")
        rows = []
        with open(input_file, 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

            for row in reader:
                # Clean toi_raw if it matches MM:SS:00 pattern
                if row['toi_raw'] and re.match(r'^\d+:\d+:\d+$', row['toi_raw']):
                    # Remove the trailing :00
                    row['toi_raw'] = ':'.join(row['toi_raw'].split(':')[:2])
                rows.append(row)

        print(f"Writing cleaned data to {output_file}...")
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

        print(f"✓ Successfully cleaned toi_raw column in {output_file}")

    @staticmethod
    def add_engineered_features(input_file: str, output_file: str) -> None:
        """
        Add engineered features to the player game logs CSV.

        Args:
            input_file: Input CSV file path
            output_file: Output CSV file path with engineered features
        """
        print(f"Reading {input_file}...")
        df = pd.read_csv(input_file)

        print(f"Initial rows: {len(df)}")

        # Filter out rows with missing shots or toi_raw
        df = df.dropna(subset=['shots', 'toi_raw'])
        print(f"After filtering missing shots/toi_raw: {len(df)}")

        # Convert toi_raw (MM:SS) to decimal minutes
        def toi_to_minutes(toi_str):
            if pd.isna(toi_str):
                return None
            parts = str(toi_str).split(':')
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = int(parts[1])
                return minutes + seconds / 60.0
            return None

        df['toi_minutes'] = df['toi_raw'].apply(toi_to_minutes)

        # Filter out rows where toi_minutes couldn't be calculated
        df = df.dropna(subset=['toi_minutes'])
        print(f"After converting TOI to minutes: {len(df)}")

        # Sort by player_id and game_date
        df = df.sort_values(['player_id', 'game_date']).reset_index(drop=True)

        # Initialize new feature columns
        feature_cols = [
            'shots_last1', 'shots_last5_sum', 'shots_last5_avg', 'toi_last5_sum',
            'shots_per60_last5', 'shots_last10_sum', 'shots_last10_avg',
            'toi_last10_sum', 'shots_per60_last10', 'shots_season_to_date',
            'toi_season_to_date', 'shots_per60_season_to_date', 'games_played_so_far'
        ]

        for col in feature_cols:
            df[col] = 0.0

        print("Calculating engineered features for each player...")

        # Group by player and calculate features
        for player_id in df['player_id'].unique():
            player_mask = df['player_id'] == player_id
            player_indices = df[player_mask].index.tolist()

            for i, idx in enumerate(player_indices):
                # Previous games for this player
                prev_indices = player_indices[:i]

                if len(prev_indices) == 0:
                    # First game - all features are 0
                    df.loc[idx, 'games_played_so_far'] = 0
                    continue

                prev_games = df.loc[prev_indices]

                # games_played_so_far
                df.loc[idx, 'games_played_so_far'] = len(prev_indices)

                # shots_last1
                df.loc[idx, 'shots_last1'] = prev_games.iloc[-1]['shots']

                # Last 5 games features
                last5_games = prev_games.tail(5)
                df.loc[idx, 'shots_last5_sum'] = last5_games['shots'].sum()
                df.loc[idx, 'shots_last5_avg'] = last5_games['shots'].mean()
                df.loc[idx, 'toi_last5_sum'] = last5_games['toi_minutes'].sum()
                if last5_games['toi_minutes'].sum() > 0:
                    df.loc[idx, 'shots_per60_last5'] = (
                        60 * last5_games['shots'].sum() / last5_games['toi_minutes'].sum()
                    )

                # Last 10 games features
                last10_games = prev_games.tail(10)
                df.loc[idx, 'shots_last10_sum'] = last10_games['shots'].sum()
                df.loc[idx, 'shots_last10_avg'] = last10_games['shots'].mean()
                df.loc[idx, 'toi_last10_sum'] = last10_games['toi_minutes'].sum()
                if last10_games['toi_minutes'].sum() > 0:
                    df.loc[idx, 'shots_per60_last10'] = (
                        60 * last10_games['shots'].sum() / last10_games['toi_minutes'].sum()
                    )

                # Season to date features
                df.loc[idx, 'shots_season_to_date'] = prev_games['shots'].sum()
                df.loc[idx, 'toi_season_to_date'] = prev_games['toi_minutes'].sum()
                if prev_games['toi_minutes'].sum() > 0:
                    df.loc[idx, 'shots_per60_season_to_date'] = (
                        60 * prev_games['shots'].sum() / prev_games['toi_minutes'].sum()
                    )

        print(f"Writing {len(df)} rows to {output_file}...")
        df.to_csv(output_file, index=False)

        print(f"✓ Successfully created engineered features in {output_file}")
        print(f"New columns added: {', '.join(feature_cols)}")

    def build_team_game_stats_from_csvs(
        self,
        input_files: List[str],
        output_file: str = "team_game_stats.csv"
    ) -> None:
        """
        Build team game stats CSV by fetching boxscores for all unique games in the input CSVs.
        Only fetches new games that aren't already in the output file.

        Args:
            input_files: List of player game log CSV files to extract game_ids from
            output_file: Output CSV file path for team stats (default: "team_game_stats.csv")
        """
        print("="*60)
        print("BUILDING TEAM GAME STATS")
        print("="*60)

        # Load existing team stats if the file exists
        existing_game_ids = set()
        existing_rows = []
        import os

        if os.path.exists(output_file):
            print(f"\nLoading existing team stats from {output_file}...")
            existing_df = pd.read_csv(output_file)
            existing_game_ids = set(existing_df['game_id'].unique())
            existing_rows = existing_df.to_dict('records')
            print(f"  Found {len(existing_game_ids)} games already in {output_file}")
        else:
            print(f"\n{output_file} does not exist - will create new file")

        # Get all unique game_ids from the input files
        all_game_ids = set()
        for file in input_files:
            print(f"\nReading {file}...")
            df = pd.read_csv(file)
            game_ids = df['game_id'].unique()
            all_game_ids.update(game_ids)
            print(f"  Found {len(game_ids)} unique games")

        # Filter to only NEW games that need to be fetched
        new_game_ids = sorted(list(all_game_ids - existing_game_ids))
        print(f"\nTotal unique games across all files: {len(all_game_ids)}")
        print(f"Games already in {output_file}: {len(existing_game_ids)}")
        print(f"NEW games to fetch: {len(new_game_ids)}")

        if len(new_game_ids) == 0:
            print(f"\n✓ No new games to fetch - {output_file} is up to date!")
            return

        # CSV headers for team stats
        headers = [
            'game_id', 'game_date', 'team_abbrev',
            'home_away', 'shots_for', 'shots_against',
            'goals_for', 'goals_against'
        ]

        new_rows = []
        total_new_games = len(new_game_ids)
        errors = 0

        print("\nFetching boxscores for NEW games only...")
        for idx, game_id in enumerate(new_game_ids, 1):
            if idx % 50 == 0:
                print(f"  Progress: {idx}/{total_new_games} games ({idx/total_new_games*100:.1f}%)")

            boxscore = self.get_boxscore(game_id)

            if not boxscore:
                errors += 1
                continue

            try:
                # Extract game date
                game_date = boxscore.get('gameDate', '')

                # Extract team stats for both home and away teams
                home_team = boxscore.get('homeTeam', {})
                away_team = boxscore.get('awayTeam', {})

                # Home team row
                home_abbrev = home_team.get('abbrev', '')
                home_sog = home_team.get('sog', 0)
                home_score = home_team.get('score', 0)
                away_sog = away_team.get('sog', 0)
                away_score = away_team.get('score', 0)

                if home_abbrev:
                    new_rows.append({
                        'game_id': game_id,
                        'game_date': game_date,
                        'team_abbrev': home_abbrev,
                        'home_away': 'home',
                        'shots_for': home_sog,
                        'shots_against': away_sog,
                        'goals_for': home_score,
                        'goals_against': away_score
                    })

                # Away team row
                away_abbrev = away_team.get('abbrev', '')

                if away_abbrev:
                    new_rows.append({
                        'game_id': game_id,
                        'game_date': game_date,
                        'team_abbrev': away_abbrev,
                        'home_away': 'away',
                        'shots_for': away_sog,
                        'shots_against': home_sog,
                        'goals_for': away_score,
                        'goals_against': home_score
                    })

            except Exception as e:
                print(f"  Error processing game {game_id}: {e}")
                errors += 1
                continue

        print(f"\n✓ Successfully fetched {len(new_game_ids) - errors}/{len(new_game_ids)} new games")
        if errors > 0:
            print(f"  {errors} games had errors")

        # Combine existing rows with new rows
        all_rows = existing_rows + new_rows

        print(f"\nWriting {len(all_rows)} team-game records to {output_file}...")
        print(f"  {len(existing_rows)} existing + {len(new_rows)} new = {len(all_rows)} total")
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(all_rows)

        print(f"✓ Successfully updated {output_file}")

    def close(self):
        """Close the session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == "__main__":
    with NHLAPIClient() as client:
        # Export all player game logs for 2023-2024 regular season
        client.export_all_player_game_logs_to_csv(
            season_id="20232024",
            game_type=2,
            output_file="player_game_logs_2023_2024.csv"
        )