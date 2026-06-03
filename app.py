import streamlit as st
from data_loader import load_data

# Page configuration
st.set_page_config(
    page_title="IPL Data Analysis Platform",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Default theme (light mode)
st.session_state.theme = 'light'

# Load data with caching
@st.cache_data
def load_cached_data(version=1):
    return load_data()

df = load_cached_data()

# Check if data is empty and show error if so
if df.empty:
    st.error("No data available. Please check the IPL.csv file in the project directory.")
    st.stop()

# Enhanced sidebar filters
st.sidebar.header("🔍 Filters")

# Year filter - Multiple selection
all_years = sorted(df['year'].unique())
selected_years = st.sidebar.multiselect(
    "Select Years",
    options=all_years,
    default=[],
    key="selected_years",
    help="Leave empty to select all years"
)

# Team filter - Multiple selection
all_teams = sorted(df['batting_team'].unique())
selected_teams = st.sidebar.multiselect(
    "Select Teams",
    options=all_teams,
    default=[],
    key="selected_teams",
    help="Leave empty to select all teams"
)

# Additional filters
st.sidebar.header("⚙️ Advanced Filters")
selected_venue = st.sidebar.selectbox(
    "Venue",
    options=[None] + sorted(df['venue'].unique()),
    format_func=lambda x: "All Venues" if x is None else x,
    key="selected_venue"
)

# Phase filter
phase_options = [None, 'Powerplay', 'Middle', 'Death']
selected_phase = st.sidebar.selectbox(
    "Match Phase",
    options=phase_options,
    format_func=lambda x: "All Phases" if x is None else x,
    key="selected_phase"
)

# Display data info in sidebar
st.sidebar.header("📊 Data Info")
st.sidebar.info(f"Total Records: {len(df):,}")
st.sidebar.info(f"Total Matches: {df['match_id'].nunique():,}")
st.sidebar.info(f"Years Available: {len(all_years)} ({min(all_years)}-{max(all_years)})")
st.sidebar.info(f"Teams Available: {len(all_teams)}")

# Define pages
dashboard = st.Page("pages/dashboard.py", title="📊 Dashboard", icon=":material/dashboard:")
team_analysis = st.Page("pages/team_analysis.py", title="🏆 Team Analysis", icon=":material/groups:")
player_analysis = st.Page("pages/player_analysis.py", title="👤 Player Analysis", icon=":material/person:")
match_analysis = st.Page("pages/match_analysis.py", title="🎯 Match Analysis", icon=":material/sports_cricket:")
trends = st.Page("pages/trends.py", title="📈 Trends", icon=":material/trending_up:")

# Navigation
pg = st.navigation({
    "Main": [dashboard],
    "Analysis": [team_analysis, player_analysis, match_analysis, trends]
})

# Run the selected page
pg.run()
