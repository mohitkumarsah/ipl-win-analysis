import pandas as pd
import numpy as np

def calculate_batting_stats(df, player_name):
    """Calculate batting statistics for a player"""
    player_df = df[df['batter'] == player_name]
    
    if player_df.empty:
        # Return default stats for player with no data
        return {
            'matches': 0,
            'runs': 0,
            'balls': 0,
            'dismissals': 0,
            'average': float('nan'),
            'strike_rate': float('nan')
        }
    
    runs = pd.to_numeric(player_df['runs_batter'], errors='coerce').sum()
    balls = pd.to_numeric(player_df['balls_faced'], errors='coerce').sum()
    dismissals = pd.to_numeric(player_df['player_out'], errors='coerce').sum()  # Changed from count() to sum() to count actual dismissals
    
    stats = {
        'matches': player_df['match_id'].nunique(),
        'runs': runs,
        'balls': balls,
        'dismissals': dismissals,
        'average': runs / dismissals if dismissals > 0 else float('nan'),
        'strike_rate': (runs / balls) * 100 if balls > 0 else float('nan'),
        'fours': player_df[player_df['runs_batter'] == 4].shape[0],
        'sixes': player_df[player_df['runs_batter'] == 6].shape[0],
        'fifties': ((player_df.groupby('match_id')['runs_batter'].sum().cumsum()) // 50).sum(),
        'hundreds': ((player_df.groupby('match_id')['runs_batter'].sum().cumsum()) // 100).sum()
    }
    
    return stats

def calculate_bowling_stats(df, player_name):
    """Calculate bowling statistics for a player"""
    player_df = df[df['bowler'] == player_name]
    
    if player_df.empty:
        # Return default stats for player with no data
        return {
            'matches': 0,
            'wickets': 0,
            'runs_conceded': 0,
            'balls_bowled': 0,
            'economy': float('nan'),
            'bowling_average': float('nan'),
            'strike_rate': float('nan'),
            'maiden_overs': 0  # Placeholder - would need to implement maiden over calculation
        }
    
    runs_conceded = pd.to_numeric(player_df['runs_bowler'], errors='coerce').sum()
    balls_bowled = pd.to_numeric(player_df['valid_ball'], errors='coerce').sum()
    wickets = pd.to_numeric(player_df['bowler_wicket'], errors='coerce').sum()
    
    stats = {
        'matches': player_df['match_id'].nunique(),
        'wickets': wickets,
        'runs_conceded': runs_conceded,
        'balls_bowled': balls_bowled,
        'economy': (runs_conceded / balls_bowled) * 6 if balls_bowled > 0 else float('nan'),
        'bowling_average': runs_conceded / wickets if wickets > 0 else float('nan'),
        'strike_rate': balls_bowled / wickets if wickets > 0 else float('nan')
    }
    
    return stats

def get_team_win_loss(df, team_name):
    """Calculate win/loss record for a team"""
    if team_name not in df['batting_team'].unique() and team_name not in df['bowling_team'].unique():
        # Return default stats for team with no data
        return {
            'wins': 0,
            'losses': 0,
            'total': 0,
            'win_pct': 0
        }
    
    team_matches = df[(df['batting_team'] == team_name) | (df['bowling_team'] == team_name)]
    unique_matches = team_matches.drop_duplicates('match_id')
    
    if unique_matches.empty:
        return {
            'wins': 0,
            'losses': 0,
            'total': 0,
            'win_pct': 0
        }
    
    wins = pd.to_numeric((unique_matches['match_won_by'] == team_name).sum(), errors='coerce')
    losses = len(unique_matches) - wins  # Changed to be more explicit
    total = wins + losses
    
    return {
        'wins': wins,
        'losses': losses,
        'total': total,
        'win_pct': (wins / total) * 10 if total > 0 else 0
    }
