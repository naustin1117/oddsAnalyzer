"""
Test the new player API endpoints
"""
import requests
import json

# API configuration
BASE_URL = "http://127.0.0.1:8000"
API_KEY = "dev-key-123"
HEADERS = {"X-API-Key": API_KEY}

# Test player IDs (you can change these to test different players)
TEST_PLAYER_ID = 8475726  # Tyler Toffoli

print("="*80)
print("TESTING NHL SHOTS BETTING API - PLAYER ENDPOINTS")
print("="*80)

# Test 1: Health check (no auth required)
print("\n1. Testing health endpoint...")
try:
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Health check passed")
        print(f"   Status: {data['status']}")
        print(f"   Predictions count: {data['predictions_count']}")
    else:
        print(f"   ✗ Health check failed: {response.status_code}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    print(f"   Make sure the API is running: uvicorn api.main:app --reload")
    exit(1)

# Test 2: Get player's recent games
print(f"\n2. Testing /players/{TEST_PLAYER_ID}/recent-games...")
try:
    response = requests.get(
        f"{BASE_URL}/players/{TEST_PLAYER_ID}/recent-games?limit=10",
        headers=HEADERS
    )

    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Request successful")
        print(f"   Player: {data['player_name']} ({data['team']})")
        print(f"   Games returned: {data['games_count']}")
        print(f"\n   Recent games:")
        for i, game in enumerate(data['games'][:3], 1):  # Show first 3 games
            print(f"     {i}. {game['game_date']} vs {game['opponent']} ({game['home_away']})")
            print(f"        Shots: {game['shots']}, Goals: {game['goals']}, Assists: {game['assists']}")

        print(f"\n   Averages (last {data['games_count']} games):")
        for key, value in data['averages'].items():
            print(f"     {key}: {value}")
    elif response.status_code == 404:
        print(f"   ⚠️  Player not found (try a different player_id)")
    else:
        print(f"   ✗ Request failed: {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 3: Get player's predictions
print(f"\n3. Testing /players/{TEST_PLAYER_ID}/predictions...")
try:
    response = requests.get(
        f"{BASE_URL}/players/{TEST_PLAYER_ID}/predictions",
        headers=HEADERS
    )

    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Request successful")
        print(f"   Player: {data['player_name']}")
        print(f"   Upcoming predictions: {data['upcoming_count']}")
        print(f"   Historical predictions: {data['historical_count']}")

        if data['upcoming_count'] > 0:
            print(f"\n   Next prediction:")
            pred = data['upcoming'][0]
            print(f"     Game: {pred['away_team']} @ {pred['home_team']}")
            print(f"     Time: {pred['game_time']}")
            print(f"     Recommendation: {pred['recommendation']}")
            print(f"     Confidence: {pred['confidence']}")
            print(f"     Line: {pred['line']}")
            print(f"     Edge: {pred['edge']:.1%}")

        if data['historical_count'] > 0:
            print(f"\n   Recent historical predictions:")
            for i, pred in enumerate(data['historical'][:3], 1):  # Show first 3
                result_emoji = "✓" if pred['result'] == 'WIN' else "✗" if pred['result'] == 'LOSS' else "≈"
                print(f"     {i}. {pred['recommendation']} (Line: {pred['line']})")
                print(f"        Result: {result_emoji} {pred['result']} - Actual: {pred['actual_shots']} shots")
    elif response.status_code == 404:
        print(f"   ⚠️  No predictions found for this player")
    else:
        print(f"   ✗ Request failed: {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 4: Test with invalid API key
print(f"\n4. Testing authentication (invalid API key)...")
try:
    response = requests.get(
        f"{BASE_URL}/players/{TEST_PLAYER_ID}/recent-games",
        headers={"X-API-Key": "invalid-key"}
    )

    if response.status_code == 401:
        print(f"   ✓ Authentication working correctly (rejected invalid key)")
    else:
        print(f"   ⚠️  Unexpected response: {response.status_code}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "="*80)
print("TESTING COMPLETE")
print("="*80)
print("\nTo test with a different player, edit TEST_PLAYER_ID in the script")
print("Common player IDs:")
print("  8478420 - David Pastrnak")
print("  8475726 - Tyler Toffoli")
print("  8477934 - Auston Matthews")