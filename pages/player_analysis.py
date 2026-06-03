import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_loader import load_data
from utils import calculate_batting_stats, calculate_bowling_stats
from common_components import apply_filters, safe_calculate_rate, safe_calculate_average

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

st.title("👤 Player Performance Analysis")

# Player type selection
player_type = st.radio("Player Type", ["Batsman", "Bowler", "All-rounder"], horizontal=True)

if player_type == "Batsman":
    players = sorted(df['batter'].unique())
    player_column = 'batter'
elif player_type == "Bowler":
    players = sorted(df['bowler'].unique())
    player_column = 'bowler'
else:
    # For all-rounders, show players who have both batted and bowled significantly
    batters = df.groupby('batter')['runs_batter'].sum().reset_index()
    bowlers = df.groupby('bowler')['bowler_wicket'].sum().reset_index()
    all_rounders = set(batters[batters['runs_batter'] > 1000]['batter']) & set(bowlers[bowlers['bowler_wicket'] > 50]['bowler'])
    players = sorted(list(all_rounders)) if all_rounders else []
    player_column = 'batter'  # Default to batter for all-rounders

if not players:
    st.warning(f"No players found for {player_type} analysis.")
    st.stop()

selected_player = st.selectbox("Select Player", players)

# Filter data using common function
session_filters = {
    'selected_years': selected_years,
    'selected_teams': selected_teams,
    'selected_venue': selected_venue,
    'selected_phase': selected_phase
}

if player_type in ["Batsman", "All-rounder"]:
    player_df = df[df['batter'] == selected_player]
    player_df = apply_filters(player_df, session_filters)

    # Batting statistics
    st.subheader(f"🏏 {selected_player} - Batting Statistics")
    batting_stats = calculate_batting_stats(df, selected_player)  # Use full dataset for overall stats

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Matches", batting_stats['matches'])
    col2.metric("Total Runs", batting_stats['runs'])
    col3.metric("Average", f"{batting_stats['average']:.2f}" if pd.notna(batting_stats['average']) else "N/A")
    col4.metric("Strike Rate", f"{batting_stats['strike_rate']:.2f}" if pd.notna(batting_stats['strike_rate']) else "N/A")

    # Additional batting metrics
    if batting_stats['fours'] > 0 or batting_stats['sixes'] > 0:
        col1, col2, col3 = st.columns(3)
        col1.metric("Fours", batting_stats['fours'])
        col2.metric("Sixes", batting_stats['sixes'])
        col3.metric("Boundaries", batting_stats['fours'] + batting_stats['sixes'])

    # Batting performance by year
    st.subheader("📈 Batting Performance Over Years")
    yearly_batting = df[df['batter'] == selected_player]
    yearly_batting = apply_filters(yearly_batting, session_filters)  # Apply filters to yearly data too
    
    if not yearly_batting.empty:
        yearly_summary = yearly_batting.groupby('year').agg({
            'runs_batter': 'sum',
            'balls_faced': 'sum',
            'player_out': 'sum'  # Changed from 'count' to 'sum' to count actual dismissals
        }).reset_index()

        # Use safe calculation functions
        yearly_summary['strike_rate'] = yearly_summary.apply(lambda row: safe_calculate_rate(row['runs_batter'], row['balls_faced']), axis=1)
        yearly_summary['average'] = yearly_summary.apply(lambda row: safe_calculate_average(row['runs_batter'], row['player_out']), axis=1)

        fig = px.line(
            yearly_summary,
            x='year',
            y=['runs_batter', 'strike_rate', 'average'],
            markers=True,
            title="Batting Performance Trends",
            labels={'value': 'Value', 'variable': 'Metric'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, config={'displayModeBar': False})
    else:
        st.info("No yearly batting data available with current filters.")

    # Performance against teams
    st.subheader("⚔️ Performance Against Teams")
    against_teams = df[df['batter'] == selected_player]
    against_teams = apply_filters(against_teams, session_filters) # Apply filters to team data too
    
    if not against_teams.empty:
        against_summary = against_teams.groupby('bowling_team').agg({
            'runs_batter': 'sum',
            'balls_faced': 'sum',
            'player_out': 'sum'  # Changed from 'count' to 'sum' to count actual dismissals
        }).reset_index()

        # Use safe calculation functions
        against_summary['strike_rate'] = against_summary.apply(lambda row: safe_calculate_rate(row['runs_batter'], row['balls_faced']), axis=1)
        against_summary['average'] = against_summary.apply(lambda row: safe_calculate_average(row['runs_batter'], row['player_out']), axis=1)

        fig = px.scatter(
            against_summary,
            x='average',
            y='strike_rate',
            size='runs_batter',
            color='runs_batter',
            hover_name='bowling_team',
            title="Performance Against Different Teams",
            labels={'average': 'Average', 'strike_rate': 'Strike Rate'}
        )
        st.plotly_chart(fig, config={'displayModeBar': False})
    else:
        st.info("No team-specific batting data available with current filters.")

if player_type in ["Bowler", "All-rounder"]:
    # Apply filters to bowler data
    bowler_df = df[df['bowler'] == selected_player]
    bowler_df = apply_filters(bowler_df, session_filters)
    
    # Bowling statistics
    st.subheader(f"🎯 {selected_player} - Bowling Statistics")
    bowling_stats = calculate_bowling_stats(df, selected_player)  # Use full dataset for overall stats

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Matches", bowling_stats['matches'])
    col2.metric("Wickets", bowling_stats['wickets'])
    col3.metric("Economy", f"{bowling_stats['economy']:.2f}" if pd.notna(bowling_stats['economy']) else "N/A")
    col4.metric("Average", f"{bowling_stats['bowling_average']:.2f}" if pd.notna(bowling_stats['bowling_average']) else "N/A")

    # Bowling performance by year
    st.subheader("📈 Bowling Performance Over Years")
    yearly_bowling = df[df['bowler'] == selected_player]
    yearly_bowling = apply_filters(yearly_bowling, session_filters)  # Apply filters to yearly data too
    
    if not yearly_bowling.empty:
        yearly_bowling_summary = yearly_bowling.groupby('year').agg({
            'bowler_wicket': 'sum',
            'runs_bowler': 'sum',
            'valid_ball': 'sum'
        }).reset_index()

        # Use safe calculation functions
        yearly_bowling_summary['economy'] = yearly_bowling_summary.apply(lambda row: safe_calculate_rate(row['runs_bowler'], row['valid_ball'], 6), axis=1)
        yearly_bowling_summary['average'] = yearly_bowling_summary.apply(lambda row: safe_calculate_average(row['runs_bowler'], row['bowler_wicket']), axis=1)

        fig = px.line(
            yearly_bowling_summary,
            x='year',
            y=['bowler_wicket', 'economy', 'average'],
            markers=True,
            title="Bowling Performance Trends",
            labels={'value': 'Value', 'variable': 'Metric'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, config={'displayModeBar': False})
    else:
        st.info("No yearly bowling data available with current filters.")

# Phase-wise performance
st.subheader("🎭 Performance by Match Phase")

if player_type in ["Batsman", "All-rounder"]:
    phase_batting = df[df['batter'] == selected_player]
    phase_batting = apply_filters(phase_batting, session_filters)  # Apply filters to phase data too
    
    if not phase_batting.empty:
        phase_summary = phase_batting.groupby('phase').agg({
            'runs_batter': 'sum',
            'balls_faced': 'sum',
            'player_out': 'sum'  # Changed from 'count' to 'sum' to count actual dismissals
        }).reset_index()

        # Use safe calculation functions
        phase_summary['strike_rate'] = phase_summary.apply(lambda row: safe_calculate_rate(row['runs_batter'], row['balls_faced']), axis=1)
        phase_summary['average'] = phase_summary.apply(lambda row: safe_calculate_average(row['runs_batter'], row['player_out']), axis=1)

        fig = px.bar(
            phase_summary,
            x='phase',
            y='strike_rate',
            color='runs_batter',
            title="Batting Performance by Phase",
            labels={'strike_rate': 'Strike Rate', 'phase': 'Match Phase'}
        )
        st.plotly_chart(fig, config={'displayModeBar': False})
    else:
        st.info("No phase-specific batting data available with current filters.")

if player_type in ["Bowler", "All-rounder"]:
    phase_bowling = df[df['bowler'] == selected_player]
    phase_bowling = apply_filters(phase_bowling, session_filters)  # Apply filters to phase data too
    
    if not phase_bowling.empty:
        phase_bowling_summary = phase_bowling.groupby('phase').agg({
            'bowler_wicket': 'sum',
            'runs_bowler': 'sum',
            'valid_ball': 'sum'
        }).reset_index()

        # Use safe calculation functions
        phase_bowling_summary['economy'] = phase_bowling_summary.apply(lambda row: safe_calculate_rate(row['runs_bowler'], row['valid_ball'], 6), axis=1)

        fig = px.bar(
            phase_bowling_summary,
            x='phase',
            y='economy',
            color='bowler_wicket',
            title="Bowling Performance by Phase",
            labels={'economy': 'Economy Rate', 'phase': 'Match Phase'}
        )
        st.plotly_chart(fig, config={'displayModeBar': False})
    else:
        st.info("No phase-specific bowling data available with current filters.")
