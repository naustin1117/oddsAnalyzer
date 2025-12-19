import sys
from pathlib import Path

# Add parent directory to path to import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import json
import re
import time
from nhl_api import NHLAPIClient


def scrape_team_lineup(team_slug, opponent=None, output_file=None):
    """
    Scrape lineup information for a specific NHL team from dailyfaceoff.com

    Args:
        team_slug (str): Team slug for URL (e.g., 'chicago-blackhawks')
        opponent (str): Opponent team slug (e.g., 'boston-bruins')
        output_file (str): Path to save CSV file. If None, returns DataFrame only

    Returns:
        dict: Dictionary containing line_combinations, goalies, and injuries DataFrames
    """
    print("="*60)
    print(f"SCRAPING LINEUP FOR {team_slug.upper().replace('-', ' ')}")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Load player name to ID mapping
    try:
        player_mapping = pd.read_csv('data/player_name_to_id.csv')
        player_name_to_id = dict(zip(player_mapping['player_name'], player_mapping['player_id']))
        print(f"✓ Loaded {len(player_name_to_id)} player name mappings\n")
    except Exception as e:
        print(f"⚠️  Warning: Could not load player name mapping: {e}")
        player_name_to_id = {}

    url = f"https://www.dailyfaceoff.com/teams/{team_slug}/line-combinations"

    try:
        print(f"Fetching: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print("✓ Page fetched successfully\n")

        soup = BeautifulSoup(response.content, 'html.parser')

        # Try to find embedded JSON data
        line_combinations = []
        goalies = []
        injuries = []
        news = []

        # Look for Next.js script tag with JSON data
        script_tags = soup.find_all('script', id='__NEXT_DATA__')

        lineup_data = None

        if script_tags:
            try:
                # Parse the JSON data from Next.js
                data = json.loads(script_tags[0].string)
                lineup_data = data.get('props', {}).get('pageProps', {}).get('combinations', {})
                print("✓ Found Next.js data structure\n")
            except Exception as e:
                print(f"⚠️  Error parsing Next.js data: {e}\n")

        # If we found structured data in JSON
        if lineup_data and 'players' in lineup_data:
            print("✓ Found structured lineup data\n")
            players = lineup_data['players']

            # Process players
            for player in players:
                player_name = player.get('name', 'Unknown')
                player_id = player_name_to_id.get(player_name, None)

                player_info = {
                    'team': team_slug,
                    'opponent': opponent or '',
                    'player_id': player_id,
                    'player_name': player_name,
                    'position': player.get('positionName', ''),
                    'position_id': player.get('positionIdentifier', ''),
                    'line': player.get('groupName', ''),
                    'line_id': player.get('groupIdentifier', ''),
                    'jersey_number': player.get('jerseyNumber', ''),
                    'injury_status': player.get('injuryStatus', '') or '',
                    'game_time_decision': player.get('gameTimeDecision', False)
                }

                # Categorize player by line assignment
                if player_info['line_id'] == 'g':
                    goalies.append(player_info)
                elif player_info['line_id']:  # Has a line assignment (f1, d1, pp1, pk1, etc.)
                    line_combinations.append(player_info)
                else:  # No line assignment - scratch
                    injuries.append(player_info)

                # ALSO add to injuries if they have an injury status (independent of lineup)
                if player_info['injury_status']:
                    injuries.append(player_info)

                # Extract latest news if available
                latest_news = player.get('latestNews')
                if latest_news:
                    news_item = {
                        'team': team_slug,
                        'player_id': player_id,
                        'player_name': player_name,
                        'created_at': latest_news.get('createdAt', ''),
                        'details': latest_news.get('details', ''),
                        'fantasy_details': latest_news.get('fantasyDetails', '')
                    }
                    news.append(news_item)

        else:
            # Fallback: Parse HTML structure
            print("⚠️  Structured data not found, parsing HTML...\n")

            # Look for player cards/links
            player_links = soup.find_all('a', href=re.compile(r'/players/'))

            for link in player_links:
                player_name = link.get_text(strip=True)
                if player_name:
                    # Try to get parent container for more context
                    parent = link.find_parent('div')

                    player_info = {
                        'team': team_slug,
                        'opponent': opponent or '',
                        'player_name': player_name,
                        'position': '',
                        'group': '',
                        'jersey_number': '',
                        'games_played': 0,
                        'goals': 0,
                        'assists': 0,
                        'toi_avg': 0,
                        'injury_status': ''
                    }

                    line_combinations.append(player_info)

        # Convert to DataFrames
        df_lines = pd.DataFrame(line_combinations)
        df_goalies = pd.DataFrame(goalies)
        df_injuries = pd.DataFrame(injuries)
        df_news = pd.DataFrame(news)

        # Convert player_id columns to nullable integers (avoids .0 suffix)
        if len(df_lines) > 0 and 'player_id' in df_lines.columns:
            df_lines['player_id'] = df_lines['player_id'].astype('Int64')
        if len(df_goalies) > 0 and 'player_id' in df_goalies.columns:
            df_goalies['player_id'] = df_goalies['player_id'].astype('Int64')
        if len(df_injuries) > 0 and 'player_id' in df_injuries.columns:
            df_injuries['player_id'] = df_injuries['player_id'].astype('Int64')
        if len(df_news) > 0 and 'player_id' in df_news.columns:
            df_news['player_id'] = df_news['player_id'].astype('Int64')

        # Print summary
        print("="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Line combinations players: {len(df_lines)}")
        print(f"Goalies: {len(df_goalies)}")
        print(f"Injuries/Scratches: {len(df_injuries)}")
        print(f"Latest News: {len(df_news)}")

        # Save to CSV if output file specified
        if output_file:
            # Save all data to separate sheets/files
            base_name = output_file.replace('.csv', '')

            if len(df_lines) > 0:
                lines_file = f"{base_name}_lines.csv"
                df_lines.to_csv(lines_file, index=False)
                print(f"\n✓ Line combinations saved to: {lines_file}")

            if len(df_goalies) > 0:
                goalies_file = f"{base_name}_goalies.csv"
                df_goalies.to_csv(goalies_file, index=False)
                print(f"✓ Goalies saved to: {goalies_file}")

            if len(df_injuries) > 0:
                injuries_file = f"{base_name}_injuries.csv"
                df_injuries.to_csv(injuries_file, index=False)
                print(f"✓ Injuries saved to: {injuries_file}")

            if len(df_news) > 0:
                news_file = f"{base_name}_news.csv"
                df_news.to_csv(news_file, index=False)
                print(f"✓ Latest news saved to: {news_file}")

        # Display sample data
        if len(df_lines) > 0:
            # Filter different line types
            forwards = df_lines[df_lines['line_id'].str.startswith('f', na=False)]
            defense = df_lines[df_lines['line_id'].str.startswith('d', na=False)]
            powerplay = df_lines[df_lines['line_id'].str.startswith('pp', na=False)]
            penalty_kill = df_lines[df_lines['line_id'].str.startswith('pk', na=False)]

            # Display forwards
            if len(forwards) > 0:
                print("\n" + "="*60)
                print("FORWARDS")
                print("="*60)
                print(forwards[['player_name', 'position', 'line']].to_string(index=False))

            # Display defense
            if len(defense) > 0:
                print("\n" + "="*60)
                print("DEFENSE")
                print("="*60)
                print(defense[['player_name', 'position', 'line']].to_string(index=False))

            # Display powerplay units
            if len(powerplay) > 0:
                print("\n" + "="*60)
                print("POWERPLAY UNITS")
                print("="*60)
                print(powerplay[['player_name', 'position', 'line']].to_string(index=False))

            # Display penalty kill units
            if len(penalty_kill) > 0:
                print("\n" + "="*60)
                print("PENALTY KILL UNITS")
                print("="*60)
                print(penalty_kill[['player_name', 'position', 'line']].to_string(index=False))

        if len(df_goalies) > 0:
            print("\n" + "="*60)
            print("GOALIES")
            print("="*60)
            print(df_goalies[['player_name', 'position']].to_string(index=False))

        if len(df_injuries) > 0:
            print("\n" + "="*60)
            print("INJURIES/SCRATCHES")
            print("="*60)
            print(df_injuries[['player_name', 'position', 'injury_status']].to_string(index=False))

        if len(df_news) > 0:
            print("\n" + "="*60)
            print("LATEST NEWS")
            print("="*60)
            print(df_news[['player_name', 'created_at', 'details']].head(10).to_string(index=False))
            if len(df_news) > 10:
                print(f"\n... and {len(df_news) - 10} more news items")

        print("\n" + "="*60)
        print("COMPLETE!")
        print("="*60)

        return {
            'line_combinations': df_lines,
            'goalies': df_goalies,
            'injuries': df_injuries,
            'news': df_news
        }

    except requests.RequestException as e:
        print(f"\n✗ Error fetching page: {e}")
        return None
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def scrape_all_teams(teams_list, output_dir='data/lineups'):
    """
    Scrape lineup information for multiple teams

    Args:
        teams_list (list): List of team slugs
        output_dir (str): Directory to save CSV files

    Returns:
        dict: Dictionary of team results
    """
    from pathlib import Path

    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    results = {}

    print("="*60)
    print("SCRAPING MULTIPLE TEAMS")
    print("="*60)
    print(f"Teams to scrape: {len(teams_list)}\n")

    for i, team_slug in enumerate(teams_list, 1):
        print(f"\n[{i}/{len(teams_list)}] Processing {team_slug}...")

        output_file = f"{output_dir}/{team_slug}"
        result = scrape_team_lineup(team_slug, output_file)
        results[team_slug] = result

        # Small delay to be respectful to the server
        if i < len(teams_list):
            import time
            time.sleep(1)

    print("\n" + "="*60)
    print("ALL TEAMS SCRAPED")
    print("="*60)

    return results


# NHL team abbreviation to dailyfaceoff slug mapping
NHL_TEAM_MAPPING = {
    'ANA': 'anaheim-ducks',
    'BOS': 'boston-bruins',
    'BUF': 'buffalo-sabres',
    'CGY': 'calgary-flames',
    'CAR': 'carolina-hurricanes',
    'CHI': 'chicago-blackhawks',
    'COL': 'colorado-avalanche',
    'CBJ': 'columbus-blue-jackets',
    'DAL': 'dallas-stars',
    'DET': 'detroit-red-wings',
    'EDM': 'edmonton-oilers',
    'FLA': 'florida-panthers',
    'LAK': 'los-angeles-kings',
    'MIN': 'minnesota-wild',
    'MTL': 'montreal-canadiens',
    'NSH': 'nashville-predators',
    'NJD': 'new-jersey-devils',
    'NYI': 'new-york-islanders',
    'NYR': 'new-york-rangers',
    'OTT': 'ottawa-senators',
    'PHI': 'philadelphia-flyers',
    'PIT': 'pittsburgh-penguins',
    'SJS': 'san-jose-sharks',
    'SEA': 'seattle-kraken',
    'STL': 'st-louis-blues',
    'TBL': 'tampa-bay-lightning',
    'TOR': 'toronto-maple-leafs',
    'VAN': 'vancouver-canucks',
    'VGK': 'vegas-golden-knights',
    'WSH': 'washington-capitals',
    'WPG': 'winnipeg-jets',
    'UTA': 'utah-hockey-club'
}


def get_teams_playing_today():
    """
    Get list of teams playing today using NHL API.
    Converts UTC times to EST and filters for games actually starting today.

    Returns:
        tuple: (list of team slugs, dict mapping team slug to opponent slug)
    """
    from datetime import timezone, timedelta
    from dateutil import parser

    # Get current date in EST
    est = timezone(timedelta(hours=-5))
    now_est = datetime.now(est)
    today_est = now_est.date()

    print("="*60)
    print(f"GETTING TEAMS PLAYING ON {today_est} (EST)")
    print("="*60)
    print(f"Current time (EST): {now_est.strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Query the schedule API with today's date
    today_str = today_est.strftime('%Y-%m-%d')
    client = NHLAPIClient()
    schedule = client.get_schedule(today_str)
    client.close()

    if not schedule or 'gameWeek' not in schedule:
        print(f"No schedule data returned for {today_str}")
        return [], {}

    teams = set()
    matchups = {}  # Maps team_slug -> opponent_slug
    game_count = 0
    games_today = 0

    # Extract teams from schedule, filtering for games actually starting today in EST
    for day in schedule.get('gameWeek', []):
        for game in day.get('games', []):
            # Get the game start time in UTC
            start_time_utc_str = game.get('startTimeUTC')

            if not start_time_utc_str:
                continue

            # Parse UTC time and convert to EST
            start_time_utc = parser.parse(start_time_utc_str)
            start_time_est = start_time_utc.astimezone(est)
            game_date_est = start_time_est.date()

            # Only include games that start today in EST
            if game_date_est != today_est:
                continue

            games_today += 1
            away_team = game.get('awayTeam', {}).get('abbrev')
            home_team = game.get('homeTeam', {}).get('abbrev')

            print(f"  Game {games_today}: {away_team} @ {home_team} - {start_time_est.strftime('%I:%M %p EST')}")

            # Map teams to their opponents
            if away_team and away_team in NHL_TEAM_MAPPING:
                away_slug = NHL_TEAM_MAPPING[away_team]
                teams.add(away_slug)
                if home_team and home_team in NHL_TEAM_MAPPING:
                    matchups[away_slug] = NHL_TEAM_MAPPING[home_team]

            if home_team and home_team in NHL_TEAM_MAPPING:
                home_slug = NHL_TEAM_MAPPING[home_team]
                teams.add(home_slug)
                if away_team and away_team in NHL_TEAM_MAPPING:
                    matchups[home_slug] = NHL_TEAM_MAPPING[away_team]

            game_count += 1

    if games_today == 0:
        print(f"No games starting today ({today_est}) in EST timezone")
    else:
        print(f"\n✓ Found {games_today} games today with {len(teams)} unique teams\n")

    return sorted(list(teams)), matchups


def scrape_todays_lineups(output_dir='data'):
    """
    Scrape lineups for all teams playing today and save to 3 combined CSV files.
    Appends to existing CSV files rather than overwriting.

    Args:
        output_dir (str): Directory to save CSV files

    Returns:
        dict: Combined DataFrames for lines, goalies, and injuries
    """
    from datetime import timezone, timedelta

    # Get teams playing today and their matchups
    teams, matchups = get_teams_playing_today()

    if not teams:
        print("No teams playing today - nothing to scrape!")
        return None

    # Get current date in EST for scrape_date column
    est = timezone(timedelta(hours=-5))
    now_est = datetime.now(est)
    scrape_date = now_est.date().strftime('%Y-%m-%d')

    # Initialize lists to collect all data
    all_lines = []
    all_goalies = []
    all_injuries = []
    all_news = []

    print("="*60)
    print(f"SCRAPING LINEUPS FOR {len(teams)} TEAMS")
    print(f"Scrape Date: {scrape_date}")
    print("="*60)

    for i, team_slug in enumerate(teams, 1):
        opponent = matchups.get(team_slug)
        opponent_display = f" vs {opponent.replace('-', ' ').title()}" if opponent else ""
        print(f"\n[{i}/{len(teams)}] Scraping {team_slug}{opponent_display}...")

        result = scrape_team_lineup(team_slug, opponent=opponent, output_file=None)

        if result:
            # Add scrape_date column to each DataFrame
            if len(result['line_combinations']) > 0:
                result['line_combinations']['scrape_date'] = scrape_date
                all_lines.append(result['line_combinations'])
            if len(result['goalies']) > 0:
                result['goalies']['scrape_date'] = scrape_date
                all_goalies.append(result['goalies'])
            if len(result['injuries']) > 0:
                result['injuries']['scrape_date'] = scrape_date
                all_injuries.append(result['injuries'])
            if len(result['news']) > 0:
                result['news']['scrape_date'] = scrape_date
                all_news.append(result['news'])

        # Small delay to be respectful to the server
        if i < len(teams):
            time.sleep(1)

    # Combine all DataFrames
    df_new_lines = pd.concat(all_lines, ignore_index=True) if all_lines else pd.DataFrame()
    df_new_goalies = pd.concat(all_goalies, ignore_index=True) if all_goalies else pd.DataFrame()
    df_new_injuries = pd.concat(all_injuries, ignore_index=True) if all_injuries else pd.DataFrame()
    df_new_news = pd.concat(all_news, ignore_index=True) if all_news else pd.DataFrame()

    # Save to CSV files
    from pathlib import Path
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print("\n" + "="*60)
    print("SAVING COMBINED LINEUPS (APPENDING TO EXISTING)")
    print("="*60)

    lines_file = f"{output_dir}/lineup_lines.csv"
    goalies_file = f"{output_dir}/lineup_goalies.csv"
    injuries_file = f"{output_dir}/lineup_injuries.csv"
    news_file = f"{output_dir}/lineup_news.csv"

    # Helper function to append to CSV or create new
    def append_to_csv(df_new, file_path, dedup_columns):
        """Append new data to CSV file, avoiding duplicates"""
        if len(df_new) == 0:
            return 0, 0

        if Path(file_path).exists():
            # Read existing data
            df_existing = pd.read_csv(file_path)
            print(f"  Found existing file with {len(df_existing)} records")

            # Combine and remove duplicates
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined = df_combined.drop_duplicates(subset=dedup_columns, keep='last')

            new_records = len(df_combined) - len(df_existing)
            df_combined.to_csv(file_path, index=False)

            return len(df_combined), new_records
        else:
            # Create new file
            df_new.to_csv(file_path, index=False)
            return len(df_new), len(df_new)

    # Save lines
    if len(df_new_lines) > 0:
        total, new = append_to_csv(
            df_new_lines,
            lines_file,
            dedup_columns=['team', 'player_name', 'line_id', 'scrape_date']
        )
        print(f"✓ Lines: {total} total records ({new} new)")
    else:
        print(f"⚠️  No line combinations to save")

    # Save goalies
    if len(df_new_goalies) > 0:
        total, new = append_to_csv(
            df_new_goalies,
            goalies_file,
            dedup_columns=['team', 'player_name', 'scrape_date']
        )
        print(f"✓ Goalies: {total} total records ({new} new)")
    else:
        print(f"⚠️  No goalies to save")

    # Save injuries
    if len(df_new_injuries) > 0:
        total, new = append_to_csv(
            df_new_injuries,
            injuries_file,
            dedup_columns=['team', 'player_name', 'scrape_date']
        )
        print(f"✓ Injuries: {total} total records ({new} new)")
    else:
        print(f"⚠️  No injuries to save")

    # Save news
    if len(df_new_news) > 0:
        total, new = append_to_csv(
            df_new_news,
            news_file,
            dedup_columns=['team', 'player_name', 'created_at']
        )
        print(f"✓ News: {total} total records ({new} new)")
    else:
        print(f"⚠️  No news to save")

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Teams scraped: {len(teams)}")
    print(f"Scrape date: {scrape_date}")
    print(f"New skaters: {len(df_new_lines)}")
    print(f"New goalies: {len(df_new_goalies)}")
    print(f"New injuries: {len(df_new_injuries)}")
    print(f"New news items: {len(df_new_news)}")

    print("\n" + "="*60)
    print("COMPLETE!")
    print("="*60)

    return {
        'line_combinations': df_new_lines,
        'goalies': df_new_goalies,
        'injuries': df_new_injuries,
        'news': df_new_news
    }


if __name__ == "__main__":
    # Scrape lineups for all teams playing today
    scrape_todays_lineups(output_dir='data')

    # To scrape a specific team instead:
    # result = scrape_team_lineup(
    #     team_slug='chicago-blackhawks',
    #     output_file='data/chicago-blackhawks-lineup'
    # )