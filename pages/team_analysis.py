import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_loader import load_data
from utils import get_team_win_loss
from common_components import apply_filters, safe_calculate_rate, safe_calculate_average
from constants import MIN_VENUE_MATCHES
st.title("🏏 IPL Analysis Dashboard")
# Load data
df = load_data()

# Check if data is empty
if df.empty:
    st.error("No data available. Please check the data file.")
    st.stop()

# Get filters from session state
selected_years = st.session_state.get('selected_years', [])
selected_teams = st.session_state.get('selected_teams', [])
selected_venue = st.session_state.get('selected_venue', None)
selected_phase = st.session_state.get('selected_phase', None)

st.title("🏆 Team Performance Analysis")

# For team analysis, use the first selected team or allow selection
if selected_teams:
    selected_team = selected_teams[0] # Use first selected team
else:
    # Allow user to select a team for analysis
    available_teams = sorted(df['batting_team'].unique())
    selected_team = st.selectbox("Select Team for Analysis", available_teams, key="team_analysis_select")

if not selected_team:
    st.info("👈 Please select a team from the sidebar or above to view detailed analysis")
    st.stop()

# Filter data
team_df = df[
    (df['batting_team'] == selected_team) |
    (df['bowling_team'] == selected_team)
]

# Apply additional filters using common function
session_filters = {
    'selected_years': selected_years,
    'selected_teams': [selected_team],  # Only apply team filter for this team
    'selected_venue': selected_venue,
    'selected_phase': selected_phase
}
team_df = apply_filters(team_df, session_filters)

# Team overview with enhanced metrics
st.subheader(f"📊 {selected_team} Overview")

win_loss = get_team_win_loss(team_df, selected_team)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Matches", win_loss['total'])
with col2:
    st.metric("Wins", win_loss['wins'], delta=f"{win_loss['wins'] - win_loss['losses']}" if win_loss['total'] > 0 else None)
with col3:
    st.metric("Win Rate", f"{win_loss['win_pct']:.1f}%")
with col4:
    # Calculate average runs scored/conceded
    batting_df = team_df[team_df['batting_team'] == selected_team]
    bowling_df = team_df[team_df['bowling_team'] == selected_team]
    avg_runs_scored = batting_df['runs_total'].mean() if not batting_df.empty else 0
    avg_runs_conceded = bowling_df['runs_total'].mean() if not bowling_df.empty else 0
    net_run_rate = avg_runs_scored - avg_runs_conceded
    st.metric("Net Run Rate", f"{net_run_rate:.2f}")

# Win/Loss visualization
st.subheader("📈 Match Outcomes")

col1, col2 = st.columns(2)

with col1:
    # Pie chart
    if win_loss['total'] > 0:
        win_loss_df = pd.DataFrame({
            'Result': ['Wins', 'Losses'],
            'Count': [win_loss['wins'], win_loss['losses']]
        })

        fig = px.pie(
            win_loss_df,
            values='Count',
            names='Result',
            title="Match Results Distribution",
            color='Result',
            color_discrete_map={'Wins': '#2E8B57', 'Losses': '#DC143C'}  # More appropriate colors
        )
        st.plotly_chart(fig, config={'displayModeBar': False})
    else:
        st.info("No match data available for this team with current filters.")

with col2:
    # Win rate over time
    if not team_df.empty:
        yearly_performance = team_df.drop_duplicates('match_id').groupby('year').agg({
            'match_won_by': lambda x: (x == selected_team).sum(),
            'match_id': 'count'
        }).reset_index()

        yearly_performance['win_pct'] = (yearly_performance['match_won_by'] / yearly_performance['match_id']) * 100

        fig = px.line(
            yearly_performance,
            x='year',
            y='win_pct',
            markers=True,
            title="Win Percentage Over Years",
            labels={'win_pct': 'Win %', 'year': 'Year'}
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, config={'displayModeBar': False})
    else:
        st.info("No yearly data available for this team with current filters.")

# Performance against opponents
st.subheader("⚔️ Performance Against Opponents")

# Get all opponents
all_matches = df.drop_duplicates('match_id')
opponent_matches = all_matches[
    (all_matches['batting_team'] == selected_team) |
    (all_matches['bowling_team'] == selected_team)
]

opponents = []
win_rates = []
matches_played = []

for team in df['batting_team'].unique():
    if team != selected_team:
        # Get matches between selected team and this opponent
        team_matches = all_matches[
            ((all_matches['batting_team'] == selected_team) & (all_matches['bowling_team'] == team)) |
            ((all_matches['batting_team'] == team) & (all_matches['bowling_team'] == selected_team))
        ]

        if len(team_matches) > 0:
            wins = (team_matches['match_won_by'] == selected_team).sum()
            win_rate = (wins / len(team_matches)) * 100

            opponents.append(team)
            win_rates.append(win_rate)
            matches_played.append(len(team_matches))

if opponents:  # Only create chart if there are opponents
    opp_df = pd.DataFrame({
        'Opponent': opponents,
        'Win Rate': win_rates,
        'Matches': matches_played
    }).sort_values('Win Rate', ascending=False)

    fig = px.bar(
        opp_df,
        x='Opponent',
        y='Win Rate',
        color='Win Rate',
        color_continuous_scale='RdYlGn',
        title="Win Rate Against All Opponents",
        labels={'Win Rate': 'Win Rate (%)', 'Opponent': 'Opponent Team'}
    )
    st.plotly_chart(fig, config={'displayModeBar': False})
else:
    st.info("No opponent data available with current filters.")

# Top contributors with enhanced analysis
st.subheader("⭐ Top Contributors")

col1, col2 = st.columns(2)

with col1:
    with st.container():
        st.markdown("**🏏 Top Run Scorers**")
        batsmen = team_df[team_df['batting_team'] == selected_team]
        if not batsmen.empty:
            top_batsmen = batsmen.groupby('batter').agg({
                'runs_batter': 'sum',
                'balls_faced': 'sum',
                'player_out': 'sum'  # Changed from 'count' to 'sum' to count actual dismissals
            }).reset_index()

            # Use safe calculation functions
            top_batsmen['average'] = top_batsmen.apply(lambda row: safe_calculate_average(row['runs_batter'], row['player_out']), axis=1)
            top_batsmen['strike_rate'] = top_batsmen.apply(lambda row: safe_calculate_rate(row['runs_batter'], row['balls_faced']), axis=1)
            # Ensure numeric types for sorting
            top_batsmen['runs_batter'] = pd.to_numeric(top_batsmen['runs_batter'], errors='coerce')
            top_batsmen = top_batsmen.sort_values('runs_batter', ascending=False).head(10)

            fig = px.scatter(
                top_batsmen,
                x='average',
                y='strike_rate',
                size='runs_batter',
                color='runs_batter',
                hover_name='batter',
                title="Batsmen Performance (Size = Total Runs)",
                labels={'average': 'Average', 'strike_rate': 'Strike Rate'}
            )
            st.plotly_chart(fig, config={'displayModeBar': False})
        else:
            st.info("No batting data available for this team with current filters.")

with col2:
    with st.container():
        st.markdown("**🎯 Top Wicket Takers**")
        bowlers = team_df[team_df['bowling_team'] == selected_team]
        if not bowlers.empty:
            top_bowlers = bowlers.groupby('bowler').agg({
                'bowler_wicket': 'sum',
                'runs_bowler': 'sum',
                'valid_ball': 'sum'
            }).reset_index()

            # Use safe calculation functions
            top_bowlers['economy'] = top_bowlers.apply(lambda row: safe_calculate_rate(row['runs_bowler'], row['valid_ball'], 6), axis=1)
            top_bowlers['average'] = top_bowlers.apply(lambda row: safe_calculate_average(row['runs_bowler'], row['bowler_wicket']), axis=1)
            top_bowlers = top_bowlers.sort_values('bowler_wicket', ascending=False).head(10)

            fig = px.scatter(
                top_bowlers,
                x='average',
                y='economy',
                size='bowler_wicket',
                color='bowler_wicket',
                hover_name='bowler',
                title="Bowlers Performance (Size = Wickets)",
                labels={'average': 'Bowling Average', 'economy': 'Economy Rate'}
            )
            st.plotly_chart(fig, config={'displayModeBar': False})
        else:
            st.info("No bowling data available for this team with current filters.")

# Venue performance
st.subheader("🏟️ Venue Performance")

if not team_df.empty:
    venue_performance = team_df.drop_duplicates('match_id').groupby('venue').agg({
        'match_won_by': lambda x: (x == selected_team).sum(),
        'match_id': 'count'
    }).reset_index()

    venue_performance['win_pct'] = (venue_performance['match_won_by'] / venue_performance['match_id']) * 100
    venue_performance = venue_performance[venue_performance['match_id'] >= MIN_VENUE_MATCHES]  # Use constant for minimum matches

    if not venue_performance.empty:
        fig = px.bar(
            venue_performance,
            x='venue',
            y='win_pct',
            color='win_pct',
            color_continuous_scale='RdYlGn',
            title="Win Percentage by Venue",
            labels={'win_pct': 'Win %', 'venue': 'Venue'}
        )
        st.plotly_chart(fig, config={'displayModeBar': False})
    else:
        st.info(f"Not enough data for venue analysis (minimum {MIN_VENUE_MATCHES} matches required).")
else:
    st.info("No venue data available with current filters.")
