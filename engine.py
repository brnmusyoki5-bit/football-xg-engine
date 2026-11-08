import sqlite3
import math

# ==========================================
# 1. DATABASE & ROLLING AVERAGES ENGINE
# ==========================================

def init_db():
    conn = sqlite3.connect('football_cache.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            league TEXT,
            home_team TEXT,
            away_team TEXT,
            home_goals INTEGER,
            away_goals INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def cache_match_result(league, home_team, away_team, home_goals, away_goals):
    conn = sqlite3.connect('football_cache.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO matches (league, home_team, away_team, home_goals, away_goals)
        VALUES (?, ?, ?, ?, ?)
    ''', (league, home_team, away_team, home_goals, away_goals))
    conn.commit()
    conn.close()

def get_rolling_league_averages(league_name):
    conn = sqlite3.connect('football_cache.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT home_goals, away_goals FROM matches WHERE league = ?
    ''', (league_name,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return 1.35, 1.05  # Default fallback baseline
        
    total_matches = len(rows)
    total_home_goals = sum(row[0] for row in rows)
    total_away_goals = sum(row[1] for row in rows)
    
    league_home_avg = total_home_goals / total_matches
    league_away_avg = total_away_goals / total_matches
    
    return round(league_home_avg, 2), round(league_away_avg, 2)


# ==========================================
# 2. LIVE MATCH TRACKING & POISSON ENGINE
# ==========================================

def poisson_probability(lmbda, k):
    return (math.exp(-lmbda) * (lmbda ** k)) / math.factorial(k)

def track_live_match(league_name, home_team, away_team, pre_home_xg, pre_away_xg, elapsed_minutes, current_home_goals, current_away_goals):
    league_home_avg, league_away_avg = get_rolling_league_averages(league_name)
    
    remaining_fraction = max(0.0, (90 - elapsed_minutes) / 90.0)
    remaining_home_xg = pre_home_xg * remaining_fraction
    remaining_away_xg = pre_away_xg * remaining_fraction
    
    print(f"\n--- LIVE MATCH ENGINE: {home_team} vs {away_team} ---")
    print(f"Elapsed Time: {elapsed_minutes}' | Score: {current_home_goals} - {current_away_goals}")
    print(f"League Baselines (DB Auto-Fetched) -> Home Avg: {league_home_avg}, Away Avg: {league_away_avg}")
    print(f"Projected Remaining xG -> Home: {remaining_home_xg:.2f} | Away: {remaining_away_xg:.2f}")
    
    home_prob_no_goal = poisson_probability(remaining_home_xg, 0)
    away_prob_no_goal = poisson_probability(remaining_away_xg, 0)
    
    print(f"Probability Home scores 0 more goals: {home_prob_no_goal * 100:.1f}%")
    print(f"Probability Away scores 0 more goals: {away_prob_no_goal * 100:.1f}%")


# ==========================================
# 3. EXECUTION TEST
# ==========================================
if __name__ == "__main__":
    init_db()
    cache_match_result("English Premier League", "Arsenal", "Chelsea", 2, 1)
    
    track_live_match(
        league_name="English Premier League",
        home_team="Arsenal",
        away_team="Chelsea",
        pre_home_xg=1.65,
        pre_away_xg=1.10,
        elapsed_minutes=60,
        current_home_goals=1,
        current_away_goals=0
    )