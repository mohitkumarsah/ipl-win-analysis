import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_loader import load_data
from common_components import safe_calculate_rate, safe_calculate_average

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

st.title("🎯 Match Analysis")

# Match selection with enhanced filtering
matches = df[['match_id', 'date', 'batting_team', 'bowling_team', 'venue', 'match_won_by']].drop_duplicates('match_id')

if selected_years:
    matches = matches[matches['date'].dt.year.isin(selected_years)]
if selected_teams:
    matches = matches[
        (matches['batting_team'].isin(selected_teams)) |
        (matches['bowling_team'].isin(selected_teams))
    ]
if selected_venue:
    matches = matches[matches['venue'] == selected_venue]

# Create match options with more details
if not matches.empty:
    match_options = matches.apply(
        lambda x: f"{x['date'].strftime('%Y-%m-%d')} - {x['batting_team']} vs {x['bowling_team']} ({x['venue']}) - Winner: {x['match_won_by']}",
        axis=1
    ).tolist()
else:
    match_options = []

if not match_options:
    st.warning("No matches found with the current filters. Please adjust your selection.")
    st.stop()

selected_match = st.selectbox("Select Match", match_options)
match_id = matches.iloc[match_options.index(selected_match)]['match_id']

# Get match data
match_df = df[df['match_id'] == match_id]

# Check if match data exists
if match_df.empty:
    st.error("No data found for the selected match.")
    st.stop()

# Match summary with enhanced styling
st.subheader("📊 Match Summary")
match_info = match_df.iloc[0]

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Venue", match_info['venue'] if pd.notna(match_info['venue']) else "Unknown")
with col2:
    st.metric("Toss Winner", match_info['toss_winner'] if pd.notna(match_info['toss_winner']) else "Unknown")
with col3:
    st.metric("Toss Decision", match_info['toss_decision'] if pd.notna(match_info['toss_decision']) else "Unknown")
with col4:
    st.metric("Winner", match_info['match_won_by'] if pd.notna(match_info['match_won_by']) else "Unknown")

# Calculate match statistics
total_runs = match_df['runs_total'].sum()
total_wickets = match_df['is_wicket'].sum()
total_balls = match_df['valid_ball'].sum()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Runs", total_runs)
with col2:
    st.metric("Total Wickets", total_wickets)
with col3:
    st.metric("Total Balls", total_balls)

# Enhanced scorecards
st.subheader("🏏 Batting Scorecards")

innings = sorted(match_df['inning'].unique())

for inning in innings:
    inning_df = match_df[match_df['inning'] == inning]
    if inning_df.empty:
        continue  # Skip if no data for this inning
        
    team = inning_df.iloc[0]['batting_team']

    with st.container():
        st.markdown(f"**{team} Innings**")

        batsmen = inning_df.groupby('batter').agg({
            'runs_batter': 'sum',
            'balls_faced': 'sum',
            'player_out': 'sum'  # Changed from 'count' to 'sum' to count actual dismissals
        }).reset_index()

        # Calculate dismissal status and strike rate using safe functions
        batsmen['dismissal'] = batsmen['player_out'].apply(lambda x: 'out' if pd.notna(x) and pd.to_numeric(x, errors='coerce') > 0 else 'not out')
        batsmen['strike_rate'] = batsmen.apply(lambda row: safe_calculate_rate(row['runs_batter'], row['balls_faced']), axis=1)
        batsmen = batsmen.rename(columns={
            'batter': 'Batsman',
            'runs_batter': 'Runs',
            'balls_faced': 'Balls',
            'player_out': 'Out'
        })

        # Style the dataframe
        st.dataframe(
            batsmen[['Batsman', 'Runs', 'Balls', 'strike_rate', 'dismissal']],
            column_config={
                "Batsman": st.column_config.TextColumn("Batsman", width="medium"),
                "Runs": st.column_config.NumberColumn("Runs", format="%d"),
                "Balls": st.column_config.NumberColumn("Balls", format="%d"),
                "strike_rate": st.column_config.NumberColumn("Strike Rate", format="%.2f"),
                "dismissal": st.column_config.TextColumn("Dismissal", width="small")
            },
            hide_index=True
        )

# Bowling scorecard
st.subheader("🎯 Bowling Scorecard")

bowlers = match_df.groupby('bowler').agg({
    'runs_bowler': 'sum',
    'valid_ball': 'sum',
    'bowler_wicket': 'sum'
}).reset_index()

# Calculate economy and average using safe functions
bowlers['economy'] = bowlers.apply(lambda row: safe_calculate_rate(row['runs_bowler'], row['valid_ball'], 6), axis=1)
bowlers['average'] = bowlers.apply(lambda row: safe_calculate_average(row['runs_bowler'], row['bowler_wicket']), axis=1)

bowlers = bowlers.rename(columns={
    'bowler': 'Bowler',
    'runs_bowler': 'Runs Conceded',
    'valid_ball': 'Balls Bowled',
    'bowler_wicket': 'Wickets'
})

st.dataframe(
    bowlers[['Bowler', 'Wickets', 'Runs Conceded', 'Balls Bowled', 'economy', 'average']],
    column_config={
        "Bowler": st.column_config.TextColumn("Bowler", width="medium"),
        "Wickets": st.column_config.NumberColumn("Wickets", format="%d"),
        "Runs Conceded": st.column_config.NumberColumn("Runs Conceded", format="%d"),
        "Balls Bowled": st.column_config.NumberColumn("Balls Bowled", format="%d"),
        "economy": st.column_config.NumberColumn("Economy", format="%.2f"),
        "average": st.column_config.NumberColumn("Average", format="%.2f")
    },
    hide_index=True
)

# Run rate progression with enhanced visualization
st.subheader("📈 Run Rate Progression")

if not match_df.empty:
    run_rate = match_df.groupby(['inning', 'over']).agg({
        'runs_total': 'sum',
        'ball': 'count'
    }).reset_index()

    run_rate['cum_runs'] = run_rate.groupby('inning')['runs_total'].cumsum()
    run_rate['cum_balls'] = run_rate.groupby('inning')['ball'].cumsum()
    run_rate['run_rate'] = run_rate.apply(lambda row: safe_calculate_rate(row['cum_runs'], row['cum_balls'], 6), axis=1)

    fig = px.line(
        run_rate,
        x='over',
        y='run_rate',
        color='inning',
        markers=True,
        title="Run Rate by Over",
        labels={'inning': 'Innings', 'over': 'Over', 'run_rate': 'Run Rate'}
    )

    # Add target line for comparison
    if not run_rate.empty and not run_rate['run_rate'].dropna().empty:
        avg_run_rate = run_rate['run_rate'].mean()
        fig.add_hline(
            y=avg_run_rate,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Avg: {avg_run_rate:.2f}"
        )

    st.plotly_chart(fig, config={'displayModeBar': False})
else:
    st.info("No run rate data available for this match.")

# Wickets by over
st.subheader("🎯 Wickets Analysis")

if 'is_wicket' in match_df.columns and match_df['is_wicket'].any():
    wickets_by_over = match_df[match_df['is_wicket']].groupby(['inning', 'over']).size().reset_index(name='wickets')

    if not wickets_by_over.empty:
        fig = px.bar(
            wickets_by_over,
            x='over',
            y='wickets',
            color='inning',
            title="Wickets by Over",
            labels={'inning': 'Innings', 'over': 'Over', 'wickets': 'Wickets'}
        )

        st.plotly_chart(fig, config={'displayModeBar': False})
    else:
        st.info("No wickets data available for this match.")
else:
    st.info("No wickets data available for this match.")

# Partnership analysis
st.subheader("🤝 Partnership Analysis")

for inning in innings:
    inning_df = match_df[match_df['inning'] == inning]
    if inning_df.empty:
        continue  # Skip if no data for this inning
        
    inning_batsmen = inning_df.groupby('batter')['runs_batter'].sum().reset_index()
    inning_batsmen = inning_batsmen.sort_values('runs_batter', ascending=False)

    st.markdown(f"**{inning} Innings - Top Performers**")
    if not inning_batsmen.empty:
        st.dataframe(
            inning_batsmen.head(5),
            column_config={
                "batter": st.column_config.TextColumn("Batsman", width="medium"),
                "runs_batter": st.column_config.NumberColumn("Runs", format="%d")
            },
            hide_index=True
        )
    else:
        st.info(f"No batting data available for {inning} innings.")
