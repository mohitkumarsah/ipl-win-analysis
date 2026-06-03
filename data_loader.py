import pandas as pd
from constants import TEAM_ALIASES
import streamlit as st
import numpy as np

@st.cache_data
def load_data(deliveries_path="deliveries.csv", matches_path="matches.csv"):
    """Load and preprocess IPL data with validation"""
    try:
        # Load deliveries data
        df = pd.read_csv(deliveries_path, low_memory=False)
        # Load matches data
        matches_df = pd.read_csv(matches_path, low_memory=False)
        
        # Rename columns to match expected format
        df = df.rename(columns={
            'match_id': 'match_id',
            'inning': 'inning',
            'batting_team': 'batting_team',
            'bowling_team': 'bowling_team',
            'over': 'over',
            'ball': 'ball',
            'batsman': 'batter',
            'bowler': 'bowler',
            'batsman_runs': 'runs_batter',
            'total_runs': 'runs_total',
            'player_dismissed': 'player_dismissed',
            'dismissal_kind': 'wicket_kind'
        })
        
        # Add match_won_by from matches
        winner_dict = matches_df.set_index('id')['winner'].to_dict()
        df['match_won_by'] = df['match_id'].map(winner_dict)
        
        # Add other match info
        match_info = matches_df.set_index('id')[['city', 'venue', 'toss_winner', 'toss_decision', 'date']].to_dict('index')
        df['venue'] = df['match_id'].map(lambda x: match_info.get(x, {}).get('venue', 'Unknown'))
        df['city'] = df['match_id'].map(lambda x: match_info.get(x, {}).get('city', 'Unknown'))
        df['toss_winner'] = df['match_id'].map(lambda x: match_info.get(x, {}).get('toss_winner', 'Unknown'))
        df['toss_decision'] = df['match_id'].map(lambda x: match_info.get(x, {}).get('toss_decision', 'Unknown'))
        df['date'] = df['match_id'].map(lambda x: match_info.get(x, {}).get('date', 'Unknown'))
        
        # Add valid_ball (assuming most balls are valid, can refine later)
        df['valid_ball'] = 1  # For simplicity, all balls are valid
        
    except FileNotFoundError as e:
        st.error(f"Data file not found: {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data file: {str(e)}")
        return pd.DataFrame()
    
    # Validate required columns exist
    required_columns = ['batting_team', 'bowling_team', 'toss_winner', 'match_won_by', 'date', 'over', 'runs_batter', 'runs_total', 'valid_ball']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"Missing required columns in data: {missing_columns}")
        return df  # Return dataframe even with missing columns but warn user
    
    # Apply team aliases
    for col in ['batting_team', 'bowling_team', 'toss_winner', 'match_won_by']:
        if col in df.columns:
            df[col] = df[col].replace(TEAM_ALIASES)
    
    # Convert date column with error handling
    if 'date' in df.columns:
        # Parse date, handle different formats
        df['date'] = pd.to_datetime(df['date'], errors='coerce', dayfirst=True)
        # Remove rows with invalid dates
        df = df.dropna(subset=['date'])
        # Extract year from date
        df['year'] = df['date'].dt.year
    
    # Create additional features with error handling
    if 'runs_batter' in df.columns:
        df['runs_batter'] = pd.to_numeric(df['runs_batter'], errors='coerce')
        df['is_boundary'] = df['runs_batter'] >= 4
    else:
        df['is_boundary'] = False  # Default value if column doesn't exist
    
    if all(col in df.columns for col in ['runs_total', 'valid_ball']):
        df['runs_total'] = pd.to_numeric(df['runs_total'], errors='coerce')
        df['valid_ball'] = pd.to_numeric(df['valid_ball'], errors='coerce')
        df['is_dot'] = (df['runs_total'] == 0) & (df['valid_ball'] == 1)
    else:
        df['is_dot'] = False  # Default value if columns don't exist
    
    if 'wicket_kind' in df.columns:
        df['is_wicket'] = df['wicket_kind'].notna()
    else:
        df['is_wicket'] = False # Default value if column doesn't exist

    # Create missing columns for stats calculations
    import numpy as np
    df['bowler_wicket'] = np.where(df['is_wicket'] & df['bowler'].notna(), 1, 0)
    df['player_out'] = np.where(df['is_wicket'] & df['batter'].notna(), 1, 0)
    df['balls_faced'] = np.where(df['batter'].notna() & (df['valid_ball'] == 1), 1, 0)
    df['runs_bowler'] = np.where(df['bowler'].notna(), df['runs_total'], 0)
    
    if 'over' in df.columns:
        df['over'] = pd.to_numeric(df['over'], errors='coerce')
        df['phase'] = df['over'].apply(lambda x: 'Powerplay' if x <= 6 else ('Death' if x >= 16 else 'Middle'))
    else:
        df['phase'] = 'Unknown'  # Default value if column doesn't exist
    
    # Data cleaning: remove rows with critical missing values
    df = df.dropna(subset=['match_id', 'batter', 'bowler'], how='all')
    
    return df
