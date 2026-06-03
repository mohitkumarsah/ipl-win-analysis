# IPL Data Analysis Platform

## Overview

This is a web-based interactive dashboard built with Streamlit for analyzing Indian Premier League (IPL) cricket data. It loads historical match data from `IPL.csv` and provides visualizations and insights across multiple pages: Dashboard, Team Analysis, Player Analysis, Match Analysis, and Trends. Users can filter data by years, teams, venues, and match phases via the sidebar.

The platform helps cricket enthusiasts, analysts, and teams explore performance metrics, trends, and statistics from IPL matches.

## Features

- **Interactive Filtering**: Select years, teams, venues, and match phases to customize views.
- **Data Export**: Download summary data as CSV or top performers as Excel from the Dashboard.
- **Visualizations**: Powered by Plotly for interactive charts (line, bar, scatter, pie).
- **Responsive Design**: Wide layout with metric cards, tables, and graphs.

### Pages and Their Functions

1. **Dashboard** (`pages/dashboard.py`):
   - Overview of key metrics (total matches, active teams, average runs, total wickets).
   - Top performers charts (run scorers and wicket takers).
   - Season-wise trends (matches and average runs over years).
   - Recent matches summary table.
   - Export options for dashboard data and top performers.

2. **Team Analysis** (`pages/team_analysis.py`):
   - Team overview (wins, losses, win rate, net run rate).
   - Match outcomes pie chart and win percentage line chart over years.
   - Performance against opponents bar chart.
   - Top contributors (batsmen and bowlers scatter plots).
   - Venue performance bar chart (win % by venue, filtered by minimum matches).

3. **Player Analysis** (`pages/player_analysis.py`):
   - Select player type (Batsman, Bowler, All-rounder).
   - Player stats (matches, runs/wickets, average, strike rate/economy).
   - Performance trends over years (line chart for batting/bowling metrics).
   - Performance against teams (scatter plot for average vs strike rate/economy).
   - Phase-wise performance (bar chart for strike rate/economy by Powerplay/Middle/Death).

4. **Match Analysis** (`pages/match_analysis.py`):
   - Select specific match from filtered list.
   - Match summary (venue, toss, winner, total runs/wickets/balls).
   - Batting and bowling scorecards (tables with strike rates, economy).
   - Run rate progression line chart.
   - Wickets by over bar chart.
   - Top performers per innings table.

5. **Trends** (`pages/trends.py`):
   - Season comparison (line charts for average runs, wickets, boundary % over years).
   - Team performance trends (win % line chart for selected team).
   - Venue analysis (bar charts for average runs and wicket frequency).
   - Phase analysis (line charts for runs and wickets by Powerplay/Middle/Death over years).
   - Advanced insights (strike rate and economy trends).
   - Team comparison bar chart (top teams by win %).
   - Player impact scatter plot (all-rounders by runs and wickets).

## Project Structure

- **app.py**: Main Streamlit app with page navigation and sidebar filters.
- **data_loader.py**: Loads and preprocesses `IPL.csv` (team aliases, date parsing, derived features like phases, boundaries, dots, wickets).
- **utils.py**: 
  - `calculate_batting_stats(player_name)`: Computes batting metrics (runs, average, strike rate, boundaries, fifties/hundreds).
  - `calculate_bowling_stats(player_name)`: Computes bowling metrics (wickets, economy, average, strike rate).
  - `get_team_win_loss(team_name)`: Calculates team wins, losses, total matches, win percentage.
- **common_components.py**:
  - `apply_filters(df)`: Applies sidebar filters to DataFrame.
  - `create_metric_cards(filtered_df, original_df)`: Displays key metrics with deltas.
  - `create_top_performers_charts(filtered_df)`: Bar charts for top batsmen and bowlers.
  - `safe_calculate_average(numerator, denominator)`: Safe division for averages (handles NaN/zero).
  - `safe_calculate_rate(numerator, denominator, multiplier=100)`: Safe rate calculation (e.g., strike rate, economy).
- **constants.py**: Team name aliases for standardization and config (e.g., min matches for analysis).
- **pages/**: Individual analysis pages as listed above.
- **IPL.csv**: Input data file (ball-by-ball IPL match data; required columns: batting_team, bowling_team, etc.).

## Setup and Installation

1. **Prerequisites**:
   - Python 3.8+.
   - Install dependencies: `pip install streamlit pandas plotly openpyxl numpy`.

2. **Data Preparation**:
   - Place `IPL.csv` in the root directory. It should contain ball-by-ball data with columns like `match_id`, `date`, `batting_team`, `bowling_team`, `batter`, `bowler`, `runs_batter`, `runs_total`, `valid_ball`, `wicket_kind`, `over`, etc.
   - If columns are missing, the app will warn but attempt to run with defaults.

3. **Running the App**:
   - Navigate to the project directory: `cd e:/computer/IPL`.
   - Run: `streamlit run app.py`.
   - Open the provided URL (usually http://localhost:8501) in your browser.

4. **Development**:
   - Use VS Code for editing.
   - Auto-formatting may adjust quotes/indentation; ensure SEARCH/REPLACE matches exactly.
   - Cache data with `@st.cache_data` for performance.

## Usage

- Launch the app and use the sidebar for filters (leave empty for all data).
- Navigate via the top menu: Main (Dashboard) or Analysis (Team/Player/Match/Trends).
- Interact with charts (zoom, hover); export data where available.
- For all-rounders in Player Analysis, only players with >1000 runs and >50 wickets are shown.

## Data Processing

- **Preprocessing** (in `data_loader.py`): Handles team name variations, date conversion, creates derived columns (e.g., `is_boundary`, `is_dot`, `phase`, `bowler_wicket`, `player_out`, `balls_faced`, `runs_bowler`).
- **Validation**: Checks for required columns; returns empty DF on errors.
- **Caching**: Uses Streamlit cache for efficient reloading.

## Potential Issues and Troubleshooting

- **Missing Data**: If `IPL.csv` lacks columns, some metrics/charts may show NaN or empty. Add columns or update data_loader.py.
- **Export Errors**: Ensure `openpyxl` is installed for Excel exports.
- **Plotly Issues**: Update Plotly (`pip install --upgrade plotly`) if charts don't render.
- **Performance**: Large CSV may slow loading; consider filtering or sampling for testing.

## Contributing

- Fork the repo and create a branch for changes.
- Update documentation in README.md.
- Test with `streamlit run app.py` and verify all pages.
- Submit pull requests with clear descriptions.

## License

This project is open-source. Feel free to use and modify for non-commercial purposes.

---

For questions or issues, check the code or extend the utils/common_components for new features.
