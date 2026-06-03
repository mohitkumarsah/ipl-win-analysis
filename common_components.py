import streamlit as st
import pandas as pd
import plotly.express as px


def apply_filters(df, session_state_filters=None):
    """
    Apply filters from session state to the dataframe
    """
    if session_state_filters is None:
        session_state_filters = {
            'selected_years': st.session_state.get('selected_years', []),
            'selected_teams': st.session_state.get('selected_teams', []),
            'selected_venue': st.session_state.get('selected_venue', None),
            'selected_phase': st.session_state.get('selected_phase', None)
        }
    
    filtered_df = df.copy()
    
    # Filter by years (multiple selection)
    if session_state_filters['selected_years']:
        filtered_df = filtered_df[filtered_df['year'].isin(session_state_filters['selected_years'])]

    # Filter by teams (multiple selection)
    if session_state_filters['selected_teams']:
        filtered_df = filtered_df[
            (filtered_df['batting_team'].isin(session_state_filters['selected_teams'])) |
            (filtered_df['bowling_team'].isin(session_state_filters['selected_teams']))
        ]

    if session_state_filters['selected_venue']:
        filtered_df = filtered_df[filtered_df['venue'] == session_state_filters['selected_venue']]
    if session_state_filters['selected_phase']:
        filtered_df = filtered_df[filtered_df['phase'] == session_state_filters['selected_phase']]
    
    return filtered_df


def create_metric_cards(filtered_df, original_df):
    """
    Create standardized metric cards for dashboard
    """
    row1 = st.columns(2)
    with row1[0]:
        st.metric(
            label="Total Matches",
            value=filtered_df['match_id'].nunique(),
            delta=f"{original_df['match_id'].nunique() - filtered_df['match_id'].nunique()}" if st.session_state.get('selected_years', []) else None
        )
    with row1[1]:
        st.metric(
            label="Active Teams",
            value=filtered_df['batting_team'].nunique(),
            delta=f"{original_df['batting_team'].nunique() - filtered_df['batting_team'].nunique()}" if st.session_state.get('selected_teams', []) else None
        )
    row2 = st.columns(2)
    with row2[0]:
        avg_runs = filtered_df['runs_total'].mean()
        st.metric(
            label="Avg Runs/Match",
            value=f"{avg_runs:.1f}",
            delta=f"{avg_runs - original_df['runs_total'].mean():.1f}" if st.session_state.get('selected_years', []) else None
        )
    with row2[1]:
        total_wickets = filtered_df['is_wicket'].sum()
        st.metric(
            label="Total Wickets",
            value=total_wickets,
            delta=f"{total_wickets - original_df['is_wicket'].sum()}" if st.session_state.get('selected_years', []) else None
        )


def create_top_performers_charts(filtered_df):
    """
    Create standardized top performers charts
    """
    col1, col2 = st.columns(2)

    with col1:
        with st.container():
            st.markdown("**Top Run Scorers**")
            top_batsmen = filtered_df.groupby('batter')['runs_batter'].sum().sort_values(ascending=False).head(10)

            fig = px.bar(
                top_batsmen,
                x=top_batsmen.values,
                y=top_batsmen.index,
                orientation='h',
                title=None,
                color=top_batsmen.values,
                color_continuous_scale='Blues'
            )
            fig.update_layout(showlegend=False, height=350, autosize=True)
            st.plotly_chart(fig, config={'displayModeBar': False})

    with col2:
        with st.container():
            st.markdown("**Top Wicket Takers**")
            top_bowlers = filtered_df.groupby('bowler')['bowler_wicket'].sum().sort_values(ascending=False).head(10)

            fig = px.bar(
                top_bowlers,
                x=top_bowlers.values,
                y=top_bowlers.index,
                orientation='h',
                title=None,
                color=top_bowlers.values,
                color_continuous_scale='Reds'
            )
            fig.update_layout(showlegend=False, height=350, autosize=True)
            st.plotly_chart(fig, config={'displayModeBar': False})


def safe_calculate_average(numerator, denominator):
    """
    Safely calculate average with null handling
    """
    # Convert to numeric to handle potential string values
    numerator = pd.to_numeric(numerator, errors='coerce')
    denominator = pd.to_numeric(denominator, errors='coerce')
    if pd.isna(denominator) or denominator == 0:
        return float('nan')
    return numerator / denominator


def safe_calculate_rate(numerator, denominator, multiplier=100):
    """
    Safely calculate rate (e.g., strike rate, economy) with null handling
    """
    # Convert to numeric to handle potential string values
    numerator = pd.to_numeric(numerator, errors='coerce')
    denominator = pd.to_numeric(denominator, errors='coerce')
    if pd.isna(denominator) or denominator == 0:
        return float('nan')
    return (numerator / denominator) * multiplier
