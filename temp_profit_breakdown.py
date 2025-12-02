import pandas as pd

# Load predictions
df = pd.read_csv('data/predictions_history_v2.csv')

# Filter for verified results only
verified = df[df['result'].notna() & (df['result'] != 'UNKNOWN')].copy()

print('='*60)
print('PROFIT BREAKDOWN')
print('='*60)

# Overall stats
total_bets = len(verified)
wins = (verified['result'] == 'WIN').sum()
losses = (verified['result'] == 'LOSS').sum()
pushes = (verified['result'] == 'PUSH').sum()
total_units = verified['units_won'].sum()
win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
roi = (total_units / total_bets * 100) if total_bets > 0 else 0

print(f'\nOVERALL:')
print(f'  Total Bets: {total_bets}')
print(f'  Record: {wins}W-{losses}L-{pushes}P ({win_rate:.1f}%)')
print(f'  Total Units: {total_units:+.2f}u')
print(f'  ROI: {roi:+.1f}%')

# By confidence
print(f'\nBY CONFIDENCE LEVEL:')
for conf in ['HIGH', 'MEDIUM', 'LOW']:
    conf_bets = verified[verified['confidence'] == conf]
    if len(conf_bets) > 0:
        conf_total = len(conf_bets)
        conf_wins = (conf_bets['result'] == 'WIN').sum()
        conf_losses = (conf_bets['result'] == 'LOSS').sum()
        conf_pushes = (conf_bets['result'] == 'PUSH').sum()
        conf_units = conf_bets['units_won'].sum()
        conf_win_rate = (conf_wins / conf_total * 100)
        conf_roi = (conf_units / conf_total * 100)

        print(f'\n  {conf}:')
        print(f'    Bets: {conf_total}')
        print(f'    Record: {conf_wins}W-{conf_losses}L-{conf_pushes}P ({conf_win_rate:.1f}%)')
        print(f'    Units: {conf_units:+.2f}u')
        print(f'    ROI: {conf_roi:+.1f}%')

print('\n' + '='*60)