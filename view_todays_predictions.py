"""
View Today's HIGH Confidence Predictions

Quick script to see what bets to place today.
"""

from verify_predictions import get_recent_predictions
import pandas as pd


def view_todays_predictions(confidence='HIGH'):
    """
    Display today's predictions in a readable format.

    Args:
        confidence (str): Confidence level to view (HIGH, MEDIUM, LOW)
    """
    print("="*80)
    print(f"TODAY'S {confidence} CONFIDENCE PREDICTIONS")
    print("="*80)
    print()

    # Get today's predictions (days_ago=0)
    predictions = get_recent_predictions(confidence, days_ago=0)

    if len(predictions) == 0:
        print(f"No {confidence} confidence predictions found for today.")
        print("Run automated_daily_analysis.py to generate predictions.")
        return

    # Display by game
    games = predictions[['away_team', 'home_team']].drop_duplicates()

    for _, game in games.iterrows():
        away_team = game['away_team']
        home_team = game['home_team']

        print(f"\n{'='*80}")
        print(f"{away_team} @ {home_team}")
        print('='*80)

        game_preds = predictions[
            (predictions['away_team'] == away_team) &
            (predictions['home_team'] == home_team)
        ]

        for _, pred in game_preds.iterrows():
            print(f"\n{pred['player_name']} ({pred['team']})")
            print(f"  Line: {pred['line']}")
            print(f"  Prediction: {pred['prediction']:.2f}")
            print(f"  Edge: {pred['edge']:.1f}%")
            print(f"  📊 {pred['recommendation']}")

            # Show odds
            if 'OVER' in pred['recommendation']:
                print(f"  💰 Over {pred['line']} ({pred['over_odds']:+d})")
            elif 'UNDER' in pred['recommendation']:
                print(f"  💰 Under {pred['line']} ({pred['under_odds']:+d})")

    print("\n" + "="*80)
    print(f"Total {confidence} confidence bets: {len(predictions)}")
    print("="*80)


if __name__ == "__main__":
    import sys

    # Default to HIGH confidence
    confidence = 'HIGH'

    # Allow command line argument
    if len(sys.argv) > 1:
        confidence = sys.argv[1].upper()

    view_todays_predictions(confidence)