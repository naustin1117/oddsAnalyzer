"""
Fix inconsistent datetime formats in predictions_history_v2.csv

This script:
1. Loads the predictions CSV
2. Parses game_time (handles both old and new formats)
3. Normalizes all to standard format: YYYY-MM-DD HH:MM:SS+00:00
4. Saves back to CSV
"""

import sys
from pathlib import Path

# Add parent directory to path to import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

PREDICTIONS_FILE = 'data/predictions_history_v2.csv'


def fix_datetime_formats():
    """Normalize all datetime formats in predictions CSV."""

    print("="*80)
    print("FIXING DATETIME FORMATS IN PREDICTIONS")
    print("="*80)

    # Load the CSV
    print(f"\nLoading {PREDICTIONS_FILE}...")
    df = pd.read_csv(PREDICTIONS_FILE)
    print(f"✓ Loaded {len(df)} rows")

    # Show samples before
    print("\nSample game_time values BEFORE normalization:")
    sample_before = df['game_time'].head(10).tolist()
    for i, val in enumerate(sample_before, 1):
        print(f"  {i}. {val}")

    # Parse game_time - use format='mixed' to handle both formats
    print("\nParsing datetime values (handling mixed formats)...")
    df['game_time'] = pd.to_datetime(df['game_time'], format='mixed')

    # Convert to the standard format: 'YYYY-MM-DD HH:MM:SS+00:00'
    # This matches the older format in the CSV
    print("Converting to standard format: 'YYYY-MM-DD HH:MM:SS+00:00'")
    df['game_time'] = df['game_time'].dt.strftime('%Y-%m-%d %H:%M:%S+00:00')

    # Show samples after
    print("\nSample game_time values AFTER normalization:")
    sample_after = df['game_time'].head(10).tolist()
    for i, val in enumerate(sample_after, 1):
        print(f"  {i}. {val}")

    # Save back to CSV
    print(f"\nSaving normalized CSV to {PREDICTIONS_FILE}...")
    df.to_csv(PREDICTIONS_FILE, index=False)

    print("\n" + "="*80)
    print("✅ DONE! All datetime formats normalized")
    print("="*80)
    print(f"Total rows processed: {len(df)}")
    print(f"Format: YYYY-MM-DD HH:MM:SS+00:00")


if __name__ == '__main__':
    fix_datetime_formats()