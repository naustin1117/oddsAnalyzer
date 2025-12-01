import requests
import json


class OddsAPIClient:
    """Client for interacting with The Odds API (the-odds-api.com)"""

    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
        self.session = requests.Session()

    def get_sports(self):
        """Get list of available sports."""
        url = f"{self.base_url}/sports"
        params = {
            'apiKey': self.api_key
        }

        response = self.session.get(url, params=params)
        response.raise_for_status()

        # Print remaining requests
        if 'x-requests-remaining' in response.headers:
            print(f"Requests remaining: {response.headers['x-requests-remaining']}")
        if 'x-requests-used' in response.headers:
            print(f"Requests used: {response.headers['x-requests-used']}")

        return response.json()

    def get_events(self, sport='icehockey_nhl', date_format='iso'):
        """
        Get list of upcoming events/games for a sport.

        Args:
            sport (str): Sport key (e.g., 'icehockey_nhl')
            date_format (str): 'iso' or 'unix'

        Returns:
            list: List of events
        """
        url = f"{self.base_url}/sports/{sport}/events"
        params = {
            'apiKey': self.api_key,
            'dateFormat': date_format
        }

        response = self.session.get(url, params=params)

        # Check for errors and show detailed message
        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.text}")

        response.raise_for_status()

        # Print remaining requests
        if 'x-requests-remaining' in response.headers:
            print(f"Requests remaining: {response.headers['x-requests-remaining']}")

        return response.json()

    def get_event_odds(self, sport, event_id, regions='us', markets='h2h',
                       odds_format='american', bookmakers=None):
        """
        Get odds for a specific event/game (including player props).

        Args:
            sport (str): Sport key (e.g., 'icehockey_nhl')
            event_id (str): Event ID from get_events()
            regions (str): Comma-separated regions (e.g., 'us', 'uk', 'eu')
            markets (str): Comma-separated markets (e.g., 'player_shots_on_goal')
            odds_format (str): 'american', 'decimal', or 'fractional'
            bookmakers (str): Comma-separated bookmaker keys (optional)

        Returns:
            dict: Event odds data
        """
        url = f"{self.base_url}/sports/{sport}/events/{event_id}/odds"
        params = {
            'apiKey': self.api_key,
            'regions': regions,
            'markets': markets,
            'oddsFormat': odds_format
        }

        if bookmakers:
            params['bookmakers'] = bookmakers

        response = self.session.get(url, params=params)

        # Check for errors and show detailed message
        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.text}")

        response.raise_for_status()

        # Print remaining requests
        if 'x-requests-remaining' in response.headers:
            print(f"Requests remaining: {response.headers['x-requests-remaining']}")

        return response.json()

    def get_odds(self, sport='icehockey_nhl', regions='us', markets='h2h',
                 odds_format='american', bookmakers=None):
        """
        Get odds for a specific sport (main markets only: h2h, spreads, totals).
        For player props, use get_events() then get_event_odds().

        Args:
            sport (str): Sport key (e.g., 'icehockey_nhl')
            regions (str): Comma-separated regions (e.g., 'us', 'uk', 'eu')
            markets (str): Comma-separated markets (e.g., 'h2h', 'spreads', 'totals')
            odds_format (str): 'american', 'decimal', or 'fractional'
            bookmakers (str): Comma-separated bookmaker keys (optional)

        Returns:
            dict: Odds data
        """
        url = f"{self.base_url}/sports/{sport}/odds"
        params = {
            'apiKey': self.api_key,
            'regions': regions,
            'markets': markets,
            'oddsFormat': odds_format
        }

        if bookmakers:
            params['bookmakers'] = bookmakers

        response = self.session.get(url, params=params)

        # Check for errors and show detailed message
        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.text}")

        response.raise_for_status()

        # Print remaining requests
        if 'x-requests-remaining' in response.headers:
            print(f"Requests remaining: {response.headers['x-requests-remaining']}")

        return response.json()

    def close(self):
        """Close the session."""
        self.session.close()


def test_api():
    """Test the API connection."""
    API_KEY = '2b7aa5b8da44c20602b4aa972245c181'

    print("="*60)
    print("TESTING THE ODDS API")
    print("="*60)

    client = OddsAPIClient(API_KEY)

    try:
        # Test 1: Get available sports
        print("\nTest 1: Getting available sports...")
        print("-"*60)
        sports = client.get_sports()

        print(f"\nFound {len(sports)} sports")

        # Find NHL
        nhl_sport = None
        for sport in sports:
            if 'nhl' in sport.get('key', '').lower():
                nhl_sport = sport
                print(f"\nNHL Sport found:")
                print(f"  Key: {sport['key']}")
                print(f"  Title: {sport['title']}")
                print(f"  Active: {sport.get('active', False)}")
                print(f"  Has outrights: {sport.get('has_outrights', False)}")
                break

        if not nhl_sport:
            print("\nWarning: NHL not found in available sports")
            print("Available sports:")
            for sport in sports[:10]:
                print(f"  - {sport['key']}: {sport['title']}")
            return

        # Test 2: Get NHL odds
        print("\n" + "="*60)
        print("Test 2: Getting NHL odds...")
        print("-"*60)

        odds = client.get_odds(
            sport='icehockey_nhl',
            regions='us',
            markets='h2h,spreads,totals',
            odds_format='american'
        )

        print(f"\nFound {len(odds)} NHL games with odds")

        if len(odds) > 0:
            print("\nFirst game example:")
            game = odds[0]
            print(f"  ID: {game.get('id')}")
            print(f"  Sport: {game.get('sport_title')}")
            print(f"  Home: {game.get('home_team')}")
            print(f"  Away: {game.get('away_team')}")
            print(f"  Commence: {game.get('commence_time')}")
            print(f"  Bookmakers: {len(game.get('bookmakers', []))}")

            if game.get('bookmakers'):
                bookmaker = game['bookmakers'][0]
                print(f"\n  First bookmaker: {bookmaker.get('title')}")
                print(f"  Markets: {len(bookmaker.get('markets', []))}")

                for market in bookmaker.get('markets', []):
                    print(f"\n    Market: {market.get('key')}")
                    for outcome in market.get('outcomes', [])[:2]:
                        print(f"      {outcome.get('name')}: {outcome.get('price')}")

        print("\n" + "="*60)
        print("API TEST SUCCESSFUL!")
        print("="*60)

    except requests.exceptions.HTTPError as e:
        print(f"\nHTTP Error: {e}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    test_api()