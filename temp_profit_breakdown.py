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

# By confidence with OVER/UNDER breakdown
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

        print(f'\n  {conf} Total:')
        print(f'    Bets: {conf_total}')
        print(f'    Record: {conf_wins}W-{conf_losses}L-{conf_pushes}P ({conf_win_rate:.1f}%)')
        print(f'    Units: {conf_units:+.2f}u')
        print(f'    ROI: {conf_roi:+.1f}%')

        # OVER bets breakdown
        over_bets = conf_bets[conf_bets['recommendation'].str.contains('OVER', na=False)]
        if len(over_bets) > 0:
            over_total = len(over_bets)
            over_wins = (over_bets['result'] == 'WIN').sum()
            over_losses = (over_bets['result'] == 'LOSS').sum()
            over_pushes = (over_bets['result'] == 'PUSH').sum()
            over_units = over_bets['units_won'].sum()
            over_win_rate = (over_wins / over_total * 100)
            over_roi = (over_units / over_total * 100)

            print(f'\n  {conf} OVER:')
            print(f'    Bets: {over_total}')
            print(f'    Record: {over_wins}W-{over_losses}L-{over_pushes}P ({over_win_rate:.1f}%)')
            print(f'    Units: {over_units:+.2f}u')
            print(f'    ROI: {over_roi:+.1f}%')

        # UNDER bets breakdown
        under_bets = conf_bets[conf_bets['recommendation'].str.contains('UNDER', na=False)]
        if len(under_bets) > 0:
            under_total = len(under_bets)
            under_wins = (under_bets['result'] == 'WIN').sum()
            under_losses = (under_bets['result'] == 'LOSS').sum()
            under_pushes = (under_bets['result'] == 'PUSH').sum()
            under_units = under_bets['units_won'].sum()
            under_win_rate = (under_wins / under_total * 100)
            under_roi = (under_units / under_total * 100)

            print(f'\n  {conf} UNDER:')
            print(f'    Bets: {under_total}')
            print(f'    Record: {under_wins}W-{under_losses}L-{under_pushes}P ({under_win_rate:.1f}%)')
            print(f'    Units: {under_units:+.2f}u')
            print(f'    ROI: {under_roi:+.1f}%')

print('\n' + '='*60)