import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_loader import load_data
from utils import get_team_win_loss
from common_components import apply_filters, safe_calculate_rate, safe_calculate_average
from constants import MIN_TEAM_MATCHES
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

st.title("📈 Trends & Insights")

# Apply filters using common function
filtered_df = apply_filters(df)

# Season comparison with enhanced metrics
st.subheader("📊 Season Comparison")

col1, col2 = st.columns(2)

with col1:
    season_stats = df.groupby('year').agg({
        'match_id': 'nunique',
        'runs_total': 'mean',
        'is_wicket': 'mean'
    }).reset_index()

    season_stats = season_stats.rename(columns={
        'match_id': 'Matches',
        'runs_total': 'Avg Runs/Match',
        'is_wicket': 'Avg Wickets/Ball'
    })

    if not season_stats.empty:
        fig = px.line(
            season_stats,
            x='year',
            y=['Avg Runs/Match', 'Avg Wickets/Ball'],
            markers=True,
            title="Seasonal Trends",
            color_discrete_sequence=['#1f77b4', '#ff7f0e'],
            labels={'value': 'Value', 'variable': 'Metric'}
        )
        st.plotly_chart(fig, config={'displayModeBar': False})
    else:
        st.info("No seasonal data available.")

with col2:
    # Boundary percentage over years
    boundary_stats = df.groupby('year').agg({
        'is_boundary': 'mean'
    }).reset_index()

    boundary_stats['boundary_pct'] = boundary_stats['is_boundary'] * 100

    if not boundary_stats.empty:
        fig = px.line(
            boundary_stats,
            x='year',
            y='boundary_pct',
            markers=True,
            title="Boundary Percentage Over Years",
            labels={'boundary_pct': 'Boundary %', 'year': 'Year'}
        )
        st.plotly_chart(fig, config={'displayModeBar': False})
    else:
        st.info("No boundary data available.")

# Team performance over time
if selected_teams:
    selected_team = selected_teams[0] # Use first selected team for detailed analysis
    st.subheader(f"🏆 {selected_team} Performance Over Time")
    team_df = df[
        (df['batting_team'] == selected_team) |
        (df['bowling_team'] == selected_team)
    ]

    # Apply filters to team data
    session_filters = {
        'selected_years': selected_years,
        'selected_teams': [selected_team],  # Only apply team filter for this team
        'selected_venue': selected_venue,
        'selected_phase': selected_phase
    }
    team_df = apply_filters(team_df, session_filters)

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
            title=f"{selected_team} Win Percentage Over Years",
            labels={'win_pct': 'Win %', 'year': 'Year'}
        )
        st.plotly_chart(fig, config={'displayModeBar': False})
    else:
        st.info(f"No data available for {selected_team} with current filters.")

# Venue analysis with multiple metrics
st.subheader("🏟️ Venue Analysis")

col1, col2 = st.columns(2)

with col1:
    venue_stats = df.groupby('venue').agg({
        'runs_total': 'mean',
        'is_wicket': 'mean',
        'match_id': 'nunique'
    }).reset_index()

    # Only venues with minimum number of matches
    venue_stats = venue_stats[venue_stats['match_id'] >= MIN_TEAM_MATCHES]
    venue_stats = venue_stats.sort_values('runs_total', ascending=False).head(10)

    if not venue_stats.empty:
        fig = px.bar(
            venue_stats,
            x='venue',
            y='runs_total',
            title="Average Runs by Venue (Top 10)",
            color='runs_total',
            color_continuous_scale='Blues',
            labels={'runs_total': 'Average Runs', 'venue': 'Venue'}
        )
        st.plotly_chart(fig, config={'displayModeBar': False})
    else:
        st.info(f"Not enough data for venue analysis (minimum {MIN_TEAM_MATCHES} matches required).")

with col2:
    # Wicket frequency by venue
    venue_wicket_stats = venue_stats.sort_values('is_wicket', ascending=False).head(10)

    if not venue_wicket_stats.empty:
        fig = px.bar(
            venue_wicket_stats,
            x='venue',
            y='is_wicket',
            title="Wicket Frequency by Venue (Top 10)",
            color='is_wicket',
            color_continuous_scale='Reds',
            labels={'is_wicket': 'Wicket Frequency', 'venue': 'Venue'}
        )
        st.plotly_chart(fig, config={'displayModeBar': False})
    else:
        st.info("Not enough wicket data for venue analysis.")

# Powerplay and death overs analysis
st.subheader("⚡ Powerplay vs Death Overs Analysis")

col1, col2 = st.columns(2)

with col1:
    phase_stats = df.groupby(['year', 'phase']).agg({
        'runs_total': 'mean',
        'is_wicket': 'mean'
    }).reset_index()

    if not phase_stats.empty:
        fig = px.line(
            phase_stats,
            x='year',
            y='runs_total',
            color='phase',
            markers=True,
            title="Average Runs by Phase",
            color_discrete_map={
                'Powerplay': '#2ca02c',
                'Middle': '#ff7f0e',
                'Death': '#d62728'
            },
            labels={'runs_total': 'Average Runs', 'year': 'Year', 'phase': 'Match Phase'}
        )
        st.plotly_chart(fig, config={'displayModeBar': False})
    else:
        st.info("No phase data available.")

with col2:
    # Wicket probability by phase
    if not phase_stats.empty:
        fig = px.line(
            phase_stats,
            x='year',
            y='is_wicket',
            color='phase',
            markers=True,
            title="Wicket Probability by Phase",
            color_discrete_map={
                'Powerplay': '#2ca02c',
                'Middle': '#ff7f0e',
                'Death': '#d62728'
            },
            labels={'is_wicket': 'Wicket Probability', 'year': 'Year', 'phase': 'Match Phase'}
        )
        st.plotly_chart(fig, config={'displayModeBar': False})
    else:
        st.info("No wicket probability data available.")

# Advanced insights
st.subheader("🔍 Advanced Insights")

col1, col2 = st.columns(2)

with col1:
    # Strike rate trends
    strike_rate_trends = df.groupby('year').agg({
        'runs_batter': 'sum',
        'balls_faced': 'sum'
    }).reset_index()

    # Use safe calculation function
    strike_rate_trends['overall_strike_rate'] = strike_rate_trends.apply(lambda row: safe_calculate_rate(row['runs_batter'], row['balls_faced']), axis=1)

    if not strike_rate_trends.empty:
        fig = px.line(
            strike_rate_trends,
            x='year',
            y='overall_strike_rate',
            markers=True,
            title="Overall Strike Rate Trends",
            labels={'overall_strike_rate': 'Strike Rate', 'year': 'Year'}
        )
        st.plotly_chart(fig, config={'displayModeBar': False})
    else:
        st.info("No strike rate data available.")

with col2:
    # Economy rate trends
    economy_trends = df.groupby('year').agg({
        'runs_bowler': 'sum',
        'valid_ball': 'sum'
    }).reset_index()

    # Use safe calculation function
    economy_trends['overall_economy'] = economy_trends.apply(lambda row: safe_calculate_rate(row['runs_bowler'], row['valid_ball'], 6), axis=1)

    if not economy_trends.empty:
        fig = px.line(
            economy_trends,
            x='year',
            y='overall_economy',
            markers=True,
            title="Overall Economy Rate Trends",
            labels={'overall_economy': 'Economy Rate', 'year': 'Year'}
        )
        st.plotly_chart(fig, config={'displayModeBar': False})
    else:
        st.info("No economy rate data available.")

# Team comparison (if multiple teams selected or show top teams)
st.subheader("🏅 Team Comparison")

# Get top teams by win percentage (using full dataset to get accurate comparison)
all_matches = df.drop_duplicates('match_id')
team_comparison = all_matches.groupby('batting_team').agg({
    'match_won_by': lambda x: (x == all_matches.loc[x.index, 'batting_team']).sum(),
    'match_id': 'count'
}).reset_index()

# Only include teams with minimum number of matches
team_comparison = team_comparison[team_comparison['match_id'] >= MIN_TEAM_MATCHES]
team_comparison['win_pct'] = (team_comparison['match_won_by'] / team_comparison['match_id']) * 100
team_comparison = team_comparison.sort_values('win_pct', ascending=False).head(8)

if not team_comparison.empty:
    fig = px.bar(
        team_comparison,
        x='batting_team',
        y='win_pct',
        color='win_pct',
        title="Top Teams by Win Percentage",
        color_continuous_scale='RdYlGn',
        labels={'win_pct': 'Win %', 'batting_team': 'Team'}
    )
    st.plotly_chart(fig, config={'displayModeBar': False})
else:
    st.info(f"Not enough data for team comparison (minimum {MIN_TEAM_MATCHES} matches required).")

# Player impact analysis
st.subheader("⭐ Player Impact Analysis")

# Most valuable players (high runs + wickets)
batting_impact = df.groupby('batter').agg({
    'runs_batter': 'sum',
    'match_id': 'nunique'
}).reset_index()

bowling_impact = df.groupby('bowler').agg({
    'bowler_wicket': 'sum',
    'match_id': 'nunique'
}).reset_index()

# Find players who appear in both (all-rounders)
all_rounders = set(batting_impact['batter']) & set(bowling_impact['bowler'])
all_rounder_impact = []

for player in all_rounders:
    batting = batting_impact[batting_impact['batter'] == player]
    bowling = bowling_impact[bowling_impact['bowler'] == player]

    if not batting.empty and not bowling.empty:
        impact_score = batting['runs_batter'].iloc[0] + (bowling['bowler_wicket'].iloc[0] * 25)  # Weighted score
        all_rounder_impact.append({
            'player': player,
            'runs': batting['runs_batter'].iloc[0],
            'wickets': bowling['bowler_wicket'].iloc[0],
            'impact_score': impact_score
        })

if all_rounder_impact:
    impact_df = pd.DataFrame(all_rounder_impact).sort_values('impact_score', ascending=False).head(10)

    fig = px.scatter(
        impact_df,
        x='runs',
        y='wickets',
        size='impact_score',
        color='impact_score',
        hover_name='player',
        title="All-rounder Impact Analysis",
        labels={'runs': 'Runs', 'wickets': 'Wickets'}
    )
    st.plotly_chart(fig, config={'displayModeBar': False})
else:
    st.info("No all-rounder data available for impact analysis.")
