import pandas as pd
import streamlit as st

def implied_probability(odds):
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)

def format_odds(odds):
    if pd.isna(odds):
        return ''
    return f"+{int(odds)}" if odds > 0 else f"{int(odds)}"

def main():
    st.set_page_config(layout="wide")
    st.title('MLB Hit Prop Model - Daily Bet Recommendations')

    player_stats_file = st.file_uploader('Upload player_stats.csv', type='csv')
    betting_odds_file = st.file_uploader('Upload betting_odds.csv', type='csv')

    if player_stats_file and betting_odds_file:
        player_stats = pd.read_csv(player_stats_file)
        betting_odds = pd.read_csv(betting_odds_file)

        player_stats.columns = player_stats.columns.str.strip()
        betting_odds.columns = betting_odds.columns.str.strip()

        player_stats.rename(columns={
            'Player Name': 'Player',
            'hard_hit_percent': 'hard_hit_rate',
            'barrel_batted_rate': 'barrel_rate',
            'sweet_spot_percent': 'sweet_spot_rate',
            'line_drive_percent': 'line_drive_rate',
            'LD%': 'line_drive_rate',
            'BABIP': 'babip',
            'xSLG': 'xslg',
            'xwOBA': 'xwoba'
        }, inplace=True)

        betting_odds.rename(columns={'Player Name': 'Player'}, inplace=True)

        st.write("Player Stats Columns:", player_stats.columns.tolist())
        st.write("Betting Odds Columns:", betting_odds.columns.tolist())

        if 'last_name, first_name' in player_stats.columns:
            split_names = player_stats['last_name, first_name'].str.split(', ', expand=True)
            player_stats['Player'] = split_names[1] + ' ' + split_names[0]

        if 'Player' in player_stats.columns and 'Player' in betting_odds.columns:
            df = pd.merge(betting_odds, player_stats, on='Player', how='left')
            df['Over Odds'] = pd.to_numeric(df['Over Odds'], errors='coerce')

            df['Model_Hit_Prob'] = (
                0.55 * (df.get('xba', 0) / 0.350) +
                0.2 * (df.get('hard_hit_rate', 0) / 0.550) +
                0.1 * (df.get('line_drive_rate', 0) / 0.280) +
                0.1 * (df.get('sweet_spot_rate', 0) / 0.400) +
                0.05 * (df.get('barrel_rate', 0) / 0.180)
            )

            df['Implied_Prob'] = df['Over Odds'].apply(implied_probability)
            df['Edge_%'] = (df['Model_Hit_Prob'] - df['Implied_Prob']) * 100
            df['Recommended_Bet'] = df['Model_Hit_Prob'] > 0.37
            df['Confidence_%'] = (df['Model_Hit_Prob'] * 100)
            df['Over Odds'] = df['Over Odds'].apply(format_odds)
            df['Recommended_Bet'] = df['Recommended_Bet'].apply(lambda x: '✅' if x else '')

            output = df[['Player', 'Matchup', 'Over Odds', 'Model_Hit_Prob', 'Implied_Prob', 'Edge_%', 'Confidence_%', 'Recommended_Bet']]
            output = output.sort_values(by='Confidence_%', ascending=False)

            st.subheader('Recommended Bets')
            st.dataframe(output, use_container_width=True)

            csv = output.to_csv(index=False).encode('utf-8')
            st.download_button(
                label='Download Recommendations as CSV',
                data=csv,
                file_name='recommended_bets.csv',
                mime='text/csv'
            )
        else:
            st.error("'Player' column missing after adjustments. Please check your uploaded files.")

if __name__ == '__main__':
    main()
