#!/usr/bin/env python3
"""
One-off script to add headshot URLs to player_name_to_id.csv
NHL headshots follow the pattern: https://assets.nhle.com/mugs/nhl/latest/{player_id}.png
"""
import csv
import os
import shutil

# File path
csv_path = "data/player_name_to_id.csv"

# Create backup of original file
backup_path = csv_path.replace('.csv', '_backup.csv')
if not os.path.exists(backup_path):
    print(f"Creating backup at {backup_path}...")
    shutil.copy(csv_path, backup_path)

# Read the CSV
print(f"Reading {csv_path}...")
rows = []
with open(csv_path, 'r', newline='') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames

    # Check if headshot_url already exists
    if 'headshot_url' not in fieldnames:
        fieldnames = list(fieldnames) + ['headshot_url']

    for row in reader:
        player_id = row['player_id']
        row['headshot_url'] = f"https://assets.nhle.com/mugs/nhl/latest/{player_id}.png"
        rows.append(row)

print(f"Found {len(rows)} players")

# Write back to CSV
print(f"Writing updated CSV to {csv_path}...")
with open(csv_path, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("Done!")
print(f"\nSample rows:")
for i, row in enumerate(rows[:3]):
    print(f"{row['player_name']}: {row['headshot_url']}")