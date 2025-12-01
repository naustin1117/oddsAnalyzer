"""
Helper script to create player name -> player ID mapping.
This needs to be run once to generate the mapping file.

Note: NHL API doesn't provide player names directly, so we'll need to
fetch them from the NHL stats API.
"""

import pandas as pd
import requests
from nhl_api import NHLAPIClient


def fetch_player_names():
    """
    Fetch player names from NHL API for all players in our database.
    """
    print("Fetching player names from NHL API...")
    print("="*60)

    # Load our player IDs from the database
    df = pd.read_csv('data/player_game_logs_2025_2026_with_opponent.csv')
    unique_player_ids = df['player_id'].unique()

    print(f"Found {len(unique_player_ids)} unique players in database\n")

    mappings = []
    errors = 0

    for i, player_id in enumerate(unique_player_ids, 1):
        if i % 50 == 0:
            print(f"Progress: {i}/{len(unique_player_ids)}")

        try:
            # Fetch player info from NHL API
            url = f"https://api-web.nhle.com/v1/player/{player_id}/landing"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()

                # Extract name
                first_name = data.get('firstName', {}).get('default', '')
                last_name = data.get('lastName', {}).get('default', '')
                full_name = f"{first_name} {last_name}".strip()

                if full_name:
                    mappings.append({
                        'player_id': player_id,
                        'player_name': full_name,
                        'first_name': first_name,
                        'last_name': last_name
                    })
                    print(f"  ✓ {player_id}: {full_name}")
                else:
                    print(f"  ⚠️  {player_id}: No name found")
                    errors += 1
            else:
                print(f"  ✗ {player_id}: HTTP {response.status_code}")
                errors += 1

        except Exception as e:
            print(f"  ✗ {player_id}: Error - {e}")
            errors += 1

    # Create DataFrame
    mapping_df = pd.DataFrame(mappings)

    # Save to CSV
    output_file = 'data/player_name_to_id.csv'
    mapping_df.to_csv(output_file, index=False)

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total players: {len(unique_player_ids)}")
    print(f"Successfully mapped: {len(mappings)}")
    print(f"Errors: {errors}")
    print(f"\nSaved to: {output_file}")

    return mapping_df


if __name__ == "__main__":
    mapping_df = fetch_player_names()

    print("\nSample mappings:")
    print(mapping_df.head(10).to_string(index=False))