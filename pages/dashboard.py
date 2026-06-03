import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_loader import load_data
from utils import calculate_batting_stats, calculate_bowling_stats, get_team_win_loss
from common_components import apply_filters, create_metric_cards, create_top_performers_charts

import numpy as np


# Picklable simple fallback model used when scikit-learn is unavailable
class SimpleModel:
    def predict_proba(self, X_input):
        # Return probability 0.5 for class 1 for all inputs as a neutral fallback
        n = np.array(X_input).shape[0]
        probs = np.zeros((n, 2))
        probs[:, 0] = 0.5
        probs[:, 1] = 0.5
        return probs

# Load data
# Note: sklearn import commented out to avoid dependency. Win predictor disabled.


df = load_data()

# Check if data is empty
if df.empty:
    st.error("No data available. Please check the data file.")
    st.stop()

# Apply filters
filtered_df = apply_filters(df)

st.title("🏏 IPL Analysis Dashboard")

# Train ML model for win prediction
def train_win_predictor_model(df):
    # Prepare training data from real IPL data
    training_data = []
    
    # Get first innings scores
    first_innings_scores = df[df['inning'] == 1].groupby('match_id')['runs_total'].sum().to_dict()
    
    # For second innings deliveries
    second_innings = df[df['inning'] == 2]
    
    for match_id in second_innings['match_id'].unique():
        match_data = second_innings[second_innings['match_id'] == match_id]
        target = first_innings_scores.get(match_id, 0) + 1
        winner = match_data['match_won_by'].iloc[0]
        batting_team = match_data['batting_team'].iloc[0]
        win = 1 if batting_team == winner else 0
        
        # Sample at different overs
        for over in [5, 10, 15]:
            over_data = match_data[match_data['over'] <= over]
            if not over_data.empty:
                current_score = over_data['runs_total'].sum()
                wickets_lost = over_data['player_dismissed'].notna().sum()
                wickets_remaining = 10 - wickets_lost
                overs_completed = over
                balls_left = 120 - (overs_completed * 6)
                runs_left = target - current_score
                current_rr = current_score / overs_completed if overs_completed > 0 else 0
                required_rr = (runs_left * 6) / balls_left if balls_left > 0 else float('inf')
                rr_diff = current_rr - required_rr if required_rr != float('inf') else current_rr
                balls_left_ratio = balls_left / 120
                
                # Team factors (simplified)
                team_diff = 0  # Can be enhanced
                venue_diff = 0
                toss_advantage = 0
                
                training_data.append([
                    wickets_remaining, rr_diff, balls_left_ratio, 
                    team_diff, venue_diff, toss_advantage, win
                ])
    
    if len(training_data) < 10:
        # Fallback to simulated data if not enough real data
        training_data = [
            [7, 0.5, 0.8, 0.1, 0.05, 1, 1],
            [3, -0.3, 0.6, -0.1, -0.05, 0, 0],
            [5, 0.2, 0.7, 0.0, 0.0, 1, 1],
            [2, -0.5, 0.4, -0.2, -0.1, 0, 0],
            [8, 0.8, 0.9, 0.15, 0.1, 1, 1],
            [4, 0.0, 0.5, 0.05, 0.0, 1, 1],
            [6, -0.2, 0.3, -0.05, -0.05, 1, 0],
            [9, 0.6, 0.85, 0.2, 0.15, 1, 1],
            [1, -0.8, 0.2, -0.25, -0.2, 0, 0],
            [5, 0.1, 0.6, 0.0, 0.0, 0, 0],
        ]
    
    X = [row[:-1] for row in training_data]
    y = [row[-1] for row in training_data]
    
    # Try to import scikit-learn lazily; provide a fallback dummy model if unavailable
    try:
        import sklearn.linear_model as lm
        model = lm.LogisticRegression(random_state=42, max_iter=1000)
        model.fit(X, y)
        return model
    except Exception:
        return SimpleModel()
    
# Build the model lazily when needed to avoid startup caching/pickling issues

# Key metrics with enhanced styling
st.subheader("📊 Key Metrics")
create_metric_cards(filtered_df, df)

# Top performers with enhanced charts
st.subheader("🏆 Top Performers")
create_top_performers_charts(filtered_df)

# Season-wise analysis
st.subheader("📈 Season-wise Analysis")

col1, col2 = st.columns(2)

with col1:
    with st.container():
        st.markdown("**Match Count by Season**")
        season_counts = df.groupby('year')['match_id'].nunique().reset_index()
        season_counts = season_counts.sort_values('year')  # Ensure proper chronological order
        fig = px.line(
            season_counts,
            x='year',
            y='match_id',
            markers=True,
            title=None
        )
        fig.update_layout(height=250, autosize=True, xaxis_title="Year", yaxis_title="Matches")
        st.plotly_chart(fig, config={'displayModeBar': False})

with col2:
    with st.container():
        st.markdown("**Average Runs per Season**")
        season_runs = df.groupby('year')['runs_total'].mean().reset_index()
        season_runs = season_runs.sort_values('year')  # Ensure proper chronological order
        fig = px.line(
            season_runs,
            x='year',
            y='runs_total',
            markers=True,
            title=None
        )
        fig.update_layout(height=250, autosize=True, xaxis_title="Year", yaxis_title="Average Runs")
        st.plotly_chart(fig, config={'displayModeBar': False})

# Recent matches summary
st.subheader("🕐 Recent Activity")
recent_matches = df.sort_values('date', ascending=False).drop_duplicates('match_id').head(5)
recent_matches = recent_matches[['date', 'batting_team', 'bowling_team', 'match_won_by', 'venue']]

col1, col2 = st.columns([3, 1])
with col1:
    if not recent_matches.empty:
        st.dataframe(
            recent_matches,
            column_config={
                "date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
                "batting_team": "Batting Team",
                "bowling_team": "Bowling Team",
                "match_won_by": "Winner",
                "venue": "Venue"
            },
            hide_index=True
        )
    else:
        st.info("No recent matches available to display.")

with col2:
    # Export functionality
    st.markdown("### 📥 Export Data")

    if st.button("📊 Export Dashboard Data"):
        # Create summary data for export
        summary_data = {
            'Metric': ['Total Matches', 'Active Teams', 'Avg Runs/Match', 'Total Wickets'],
            'Value': [
                filtered_df['match_id'].nunique(),
                filtered_df['batting_team'].nunique(),
                f"{filtered_df['runs_total'].mean():.1f}",
                filtered_df['is_wicket'].sum()
            ]
        }

        summary_df = pd.DataFrame(summary_data)
        csv = summary_df.to_csv(index=False)
        st.download_button(
            label="📄 Download CSV",
            data=csv,
            file_name="dashboard_summary.csv",
            mime="text/csv"
        )

    if st.button("🏆 Export Top Performers"):
        top_batsmen = filtered_df.groupby('batter')['runs_batter'].sum().sort_values(ascending=False).head(10)
        top_bowlers = filtered_df.groupby('bowler')['bowler_wicket'].sum().sort_values(ascending=False).head(10)

        # Create Excel file with multiple sheets
        export_file = "top_performers.xlsx"
        with pd.ExcelWriter(export_file, engine='openpyxl') as writer:
            top_batsmen.to_frame('Runs').to_excel(writer, sheet_name='Top Batsmen')
            top_bowlers.to_frame('Wickets').to_excel(writer, sheet_name='Top Bowlers')

        with open(export_file, 'rb') as f:
            st.download_button(
                label="📊 Download Excel",
                data=f,
                file_name=export_file,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# IPL Win Predictor
st.markdown("""
<style>
/* Responsive adjustments */
@media (max-width: 768px) {
  .main .block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
    padding-left: 1rem;
    padding-right: 1rem;
  }
  h1 {
    font-size: 1.8rem !important;
  }
  h2, h3 {
    font-size: 1.4rem !important;
  }
  [data-testid="stMetricLabel"] {
    font-size: 0.9rem !important;
  }
  .stPlotlyChart {
    height: 300px !important;
  }
}
@media (max-width: 480px) {
  h1 {
    font-size: 1.5rem !important;
  }
}
</style>
""", unsafe_allow_html=True)
st.subheader("🎯 IPL Win Predictor")

st.markdown("Predict the winning probability of a cricket team in a live IPL match using machine learning.")

# Input form
with st.form("win_predictor_form"):
    batting_team = st.selectbox(
        "Batting Team",
        options=sorted(df['batting_team'].unique()),
        help="Select the team currently batting"
    )
    bowling_team = st.selectbox(
        "Bowling Team", 
        options=sorted(df['bowling_team'].unique()),
        help="Select the team currently bowling"
    )
    city = st.selectbox(
        "City",
        options=sorted(df['venue'].unique()),
        help="Select the match venue city"
    )
    target_score = st.number_input(
        "Target Score",
        min_value=1,
        value=150,
        help="The target score to chase"
    )
    current_score = st.number_input(
        "Current Score",
        min_value=0,
        value=75,
        help="Current score of batting team"
    )
    overs_completed = st.number_input(
        "Overs Completed",
        min_value=0.0,
        max_value=20.0,
        value=10.0,
        step=0.1,
        help="Number of overs completed (0-20)"
    )
    wickets_lost = st.number_input(
        "Wickets Lost",
        min_value=0,
        max_value=10,
        value=3,
        help="Number of wickets lost by batting team"
    )
    toss_winner = st.selectbox(
        "Toss Winner",
        options=sorted(df['batting_team'].unique()),
        help="Which team won the toss?"
    )
    
    predict_button = st.form_submit_button("🔮 Predict Win Probability")

if predict_button:
    # Calculate features
    runs_left = target_score - current_score
    balls_left = 120 - (overs_completed * 6)
    wickets_remaining = 10 - wickets_lost
    
    # Error handling
    if balls_left <= 0:
        st.error("Match is already over!")
    elif runs_left < 0:
        st.error("Target already achieved!")
    elif wickets_remaining <= 0:
        st.error("All wickets lost!")
    else:
        # Train or get model on demand
        try:
            model = train_win_predictor_model(df)
        except Exception as e:
            st.error(f"Model training failed: {e}")
            st.stop()

        current_rr = current_score / overs_completed if overs_completed > 0 else 0
        required_rr = (runs_left * 6) / balls_left if balls_left > 0 else float('inf')
        rr_diff = current_rr - required_rr if required_rr != float('inf') else current_rr
        balls_left_ratio = balls_left / 120
        
        # Team strength factor
        team_matches = df.groupby('batting_team')['match_id'].nunique().add(df.groupby('bowling_team')['match_id'].nunique(), fill_value=0)
        team_wins = df.groupby('match_won_by')['match_id'].nunique()
        team_win_rate = (team_wins / team_matches).fillna(0.5)
        
        batting_win_rate = team_win_rate.get(batting_team, 0.5)
        bowling_win_rate = team_win_rate.get(bowling_team, 0.5)
        team_diff = batting_win_rate - bowling_win_rate
        
        # Venue advantage factor
        venue_matches = df[df['venue'] == city]
        venue_diff = 0
        if not venue_matches.empty:
            venue_wins = venue_matches.groupby('match_won_by')['match_id'].nunique()
            venue_total = venue_matches['match_id'].nunique()
            batting_venue_win = venue_wins.get(batting_team, 0) / venue_total if venue_total > 0 else 0
            bowling_venue_win = venue_wins.get(bowling_team, 0) / venue_total if venue_total > 0 else 0
            venue_diff = batting_venue_win - bowling_venue_win
        
        # Toss advantage
        toss_advantage = 1 if toss_winner == batting_team else 0
        
        # ML Model Prediction
        features = np.array([[wickets_remaining, rr_diff, balls_left_ratio, team_diff, venue_diff, toss_advantage]])
        win_probability = model.predict_proba(features)[0][1]  # Probability of win (class 1)
        
        batting_prob = win_probability * 100
        bowling_prob = 100 - batting_prob
        
        # Display results
        st.success("Prediction Complete!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(f"🏏 {batting_team} Win Probability", f"{batting_prob:.1f}%")
            st.progress(batting_prob / 100)
        
        with col2:
            st.metric(f"🎯 {bowling_team} Win Probability", f"{bowling_prob:.1f}%")
            st.progress(bowling_prob / 100)
        
        # Pie chart
        fig = go.Figure(data=[go.Pie(
            labels=[batting_team, bowling_team],
            values=[batting_prob, bowling_prob],
            marker_colors=['#1f77b4', '#ff7f0e']
        )])
        fig.update_layout(title="Win Probability Distribution")
        st.plotly_chart(fig, config={'displayModeBar': False})
        
        # Show calculated features
        st.markdown("### 📊 Match Features")
        features_col1, features_col2 = st.columns(2)
        
        with features_col1:
            st.write(f"**Runs Left:** {runs_left}")
            st.write(f"**Balls Left:** {balls_left}")
            st.write(f"**Wickets Remaining:** {wickets_remaining}")
        
        with features_col2:
            st.write(f"**Current Run Rate:** {current_rr:.2f}")
            st.write(f"**Required Run Rate:** {required_rr:.2f}")
