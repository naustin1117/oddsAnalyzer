"""
Recalculate Edge using Poisson Distribution

*** ONE-TIME SCRIPT ***
This script was used to recalculate historical predictions with Poisson-based true edge.
It is NOT part of the regular workflow. Going forward, automated_daily_analysis.py
calculates true edge directly using Poisson distribution for all new predictions.

This script:
1. Reads existing predictions from predictions_history.csv (with old edge calculation)
2. Calculates true betting edge using Poisson distribution
3. Saves to predictions_history_v2.csv with new edge calculations

True Edge = Model Probability - Implied Probability
"""

import pandas as pd
from scipy.stats import poisson
import numpy as np


def odds_to_implied_prob(odds):
    """
    Convert American odds to implied probability.

    Args:
        odds (int): American odds (e.g., -180 or +150)

    Returns:
        float: Implied probability as decimal (0-1)
    """
    try:
        odds = int(odds)
        if odds > 0:
            # Positive odds: prob = 100 / (odds + 100)
            return 100.0 / (odds + 100.0)
        else:
            # Negative odds: prob = |odds| / (|odds| + 100)
            return abs(odds) / (abs(odds) + 100.0)
    except (ValueError, TypeError):
        return np.nan


def calculate_poisson_probability(prediction, line, bet_type):
    """
    Calculate probability of OVER or UNDER using Poisson distribution.

    Args:
        prediction (float): Model's predicted shots
        line (float): Betting line
        bet_type (str): 'OVER' or 'UNDER'

    Returns:
        float: Probability as decimal (0-1)
    """
    if bet_type == 'OVER':
        # P(X > line) = 1 - P(X <= line)
        return 1 - poisson.cdf(line, prediction)
    else:  # UNDER
        # P(X < line) = P(X <= line-1)
        # For 1.5 line: P(X < 1.5) = P(X <= 1) = P(X=0) + P(X=1)
        return poisson.cdf(line - 0.5, prediction)


def recalculate_predictions():
    """
    Main function to recalculate edge with Poisson distribution.
    """
    print("="*80)
    print("RECALCULATING EDGE WITH POISSON DISTRIBUTION")
    print("="*80)
    print()

    # Load existing predictions
    input_file = 'data/predictions_history.csv'
    output_file = 'data/predictions_history_v2.csv'

    print(f"Loading predictions from {input_file}...")
    df = pd.read_csv(input_file)
    print(f"✓ Loaded {len(df)} predictions")
    print()

    # Add new columns
    df['model_probability'] = np.nan
    df['implied_probability'] = np.nan
    df['true_edge'] = np.nan
    df['old_edge'] = df['edge']  # Save old edge for comparison

    print("Calculating probabilities and true edge...")

    for idx, row in df.iterrows():
        prediction = row['prediction']
        line = row['line']
        recommendation = row['recommendation']

        # Determine bet type
        if 'OVER' in recommendation:
            bet_type = 'OVER'
            relevant_odds = row['over_odds']
        elif 'UNDER' in recommendation:
            bet_type = 'UNDER'
            relevant_odds = row['under_odds']
        else:
            # NO BET
            continue

        # Calculate model probability using Poisson
        model_prob = calculate_poisson_probability(prediction, line, bet_type)

        # Calculate implied probability from odds
        implied_prob = odds_to_implied_prob(relevant_odds)

        # Calculate true edge
        true_edge = (model_prob - implied_prob) * 100  # Convert to percentage

        # Update dataframe
        df.at[idx, 'model_probability'] = model_prob
        df.at[idx, 'implied_probability'] = implied_prob
        df.at[idx, 'true_edge'] = true_edge
        df.at[idx, 'edge'] = true_edge  # Replace old edge with true edge

    print(f"✓ Calculated probabilities for {len(df)} predictions")
    print()

    # Save to new file
    print(f"Saving to {output_file}...")
    df.to_csv(output_file, index=False)
    print(f"✓ Saved to {output_file}")
    print()

    # Show comparison statistics
    print("="*80)
    print("COMPARISON: OLD EDGE vs TRUE EDGE")
    print("="*80)
    print()

    # Filter out NO BET recommendations
    df_with_bets = df[df['recommendation'] != 'NO BET'].copy()

    print(f"Total predictions with recommendations: {len(df_with_bets)}")
    print()

    # Show sample of changes
    print("Sample of edge changes:")
    print("-"*80)
    sample = df_with_bets[['player_name', 'line', 'prediction', 'recommendation',
                           'old_edge', 'true_edge', 'model_probability',
                           'implied_probability']].head(10)
    print(sample.to_string(index=False))
    print()

    # Statistics by confidence level
    print("\nAverage True Edge by Original Confidence Level:")
    print("-"*80)
    for conf in ['HIGH', 'MEDIUM', 'LOW']:
        subset = df_with_bets[df_with_bets['confidence'] == conf]
        if len(subset) > 0:
            avg_old = subset['old_edge'].mean()
            avg_true = subset['true_edge'].mean()
            print(f"{conf:8s}: Old Edge = {avg_old:6.2f}%  |  True Edge = {avg_true:6.2f}%  |  Count = {len(subset)}")

    print()
    print("="*80)
    print("COMPLETE!")
    print("="*80)
    print(f"\nNew predictions saved to: {output_file}")
    print("\nNext steps:")
    print("1. Review the true_edge column to see if thresholds need adjustment")
    print("2. Consider updating confidence levels based on true_edge instead of old_edge")
    print("3. Update automated_daily_analysis.py to use Poisson for new predictions")


if __name__ == "__main__":
    recalculate_predictions()