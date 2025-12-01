import pandas as pd
from datetime import datetime
from odds_api import OddsAPIClient
import time


def pull_daily_sog_lines(api_key, output_file='data/daily_sog_lines.csv'):
    """
    Pull all NHL player shots-on-goal lines for today's games.

    Args:
        api_key (str): The Odds API key
        output_file (str): Path to save CSV file

    Returns:
        DataFrame: All player SOG props found
    """
    print("="*60)
    print("PULLING DAILY NHL SHOTS-ON-GOAL LINES")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    client = OddsAPIClient(api_key)
    all_props = []

    try:
        # Get all NHL events
        print("Step 1: Getting NHL events...")
        events = client.get_events(sport='icehockey_nhl')
        print(f"✓ Found {len(events)} upcoming NHL games\n")

        if len(events) == 0:
            print("No games found. Check back later.")
            client.close()
            return pd.DataFrame()

        # Get player props for each event
        print("Step 2: Fetching player SOG props for each game...")
        print("-"*60)

        games_with_props = 0
        total_players = 0

        for i, event in enumerate(events, 1):
            away_team = event['away_team']
            home_team = event['home_team']
            game_time = event['commence_time']
            event_id = event['id']

            print(f"\n{i}. {away_team} @ {home_team}")
            print(f"   Time: {game_time}")

            # Small delay to avoid rate limiting
            if i > 1:
                time.sleep(0.5)

            try:
                # Get SOG props
                event_odds = client.get_event_odds(
                    sport='icehockey_nhl',
                    event_id=event_id,
                    regions='us',
                    markets='player_shots_on_goal',
                    odds_format='american'
                )

                bookmakers = event_odds.get('bookmakers', [])

                if len(bookmakers) == 0:
                    print(f"   ⚠️  No SOG props available yet")
                    continue

                games_with_props += 1
                print(f"   ✓ Found props from {len(bookmakers)} bookmakers")

                # Extract all props from all bookmakers
                for bookmaker in bookmakers:
                    bookmaker_name = bookmaker['title']

                    for market in bookmaker.get('markets', []):
                        if market['key'] != 'player_shots_on_goal':
                            continue

                        for outcome in market.get('outcomes', []):
                            player_name = outcome.get('description', 'Unknown')
                            over_under = outcome.get('name')  # 'Over' or 'Under'
                            line = outcome.get('point', 0)
                            odds = outcome.get('price', 0)

                            all_props.append({
                                'date': game_time.split('T')[0],
                                'game_time': game_time,
                                'away_team': away_team,
                                'home_team': home_team,
                                'event_id': event_id,
                                'bookmaker': bookmaker_name,
                                'player_name': player_name,
                                'over_under': over_under,
                                'line': line,
                                'odds': odds
                            })

                            total_players += 1

            except Exception as e:
                print(f"   ✗ Error: {e}")

        # Create DataFrame
        if len(all_props) == 0:
            print("\n" + "="*60)
            print("NO PROPS FOUND")
            print("="*60)
            print("\nPlayer props may not be posted yet.")
            print("Try running again 1-2 hours before game time.")
            return pd.DataFrame()

        df = pd.DataFrame(all_props)

        # Pivot to get Over/Under on same row
        df_pivot = df.pivot_table(
            index=['date', 'game_time', 'away_team', 'home_team', 'event_id',
                   'bookmaker', 'player_name', 'line'],
            columns='over_under',
            values='odds',
            aggfunc='first'
        ).reset_index()

        # Rename columns
        df_pivot.columns.name = None
        if 'Over' in df_pivot.columns and 'Under' in df_pivot.columns:
            df_pivot = df_pivot.rename(columns={'Over': 'over_odds', 'Under': 'under_odds'})

        # Sort by game time and player name
        df_pivot = df_pivot.sort_values(['game_time', 'player_name'])

        # Save to CSV
        df_pivot.to_csv(output_file, index=False)

        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Games with props: {games_with_props}/{len(events)}")
        print(f"Total player props: {total_players}")
        print(f"Unique players: {df_pivot['player_name'].nunique()}")
        print(f"Bookmakers: {df_pivot['bookmaker'].nunique()}")
        print(f"\nSaved to: {output_file}")

        # Show sample
        print("\n" + "="*60)
        print("SAMPLE PROPS (first 5)")
        print("="*60)
        print(df_pivot[['player_name', 'line', 'over_odds', 'under_odds', 'bookmaker']].head(5).to_string(index=False))

        print("\n" + "="*60)
        print("COMPLETE!")
        print("="*60)

        return df_pivot

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()
    finally:
        client.close()


def get_consensus_lines(props_df):
    """
    Get consensus lines by averaging across bookmakers.

    Args:
        props_df (DataFrame): Output from pull_daily_sog_lines()

    Returns:
        DataFrame: Consensus lines per player
    """
    if len(props_df) == 0:
        return pd.DataFrame()

    # Group by player and calculate consensus
    consensus = props_df.groupby(['player_name', 'away_team', 'home_team']).agg({
        'line': 'mean',
        'over_odds': 'mean',
        'under_odds': 'mean',
        'bookmaker': 'count'
    }).reset_index()

    consensus = consensus.rename(columns={'bookmaker': 'num_bookmakers'})
    consensus = consensus.sort_values('line', ascending=False)

    return consensus


if __name__ == "__main__":
    API_KEY = '2b7aa5b8da44c20602b4aa972245c181'

    # Pull today's lines
    props_df = pull_daily_sog_lines(API_KEY)

    # If props were found, show consensus
    if len(props_df) > 0:
        print("\n\n" + "="*60)
        print("CONSENSUS LINES (averaged across bookmakers)")
        print("="*60)

        consensus = get_consensus_lines(props_df)
        print(consensus.to_string(index=False))