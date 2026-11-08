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

def seed_initial_data():
    """Populates initial matches so rolling averages have data to calculate instantly."""
    conn = sqlite3.connect('football_cache.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM matches")
    count = cursor.fetchone()[0]
    conn.close()
    
    if count == 0:
        sample_matches = [
            ("EPL", "Arsenal", "Wolves", 2, 0),
            ("EPL", "Man City", "Bournemouth", 3, 1),
            ("EPL", "Liverpool", "Brighton", 2, 2),
            ("EPL", "Chelsea", "Fulham", 1, 0),
            ("EPL", "Newcastle", "Tottenham", 2, 1),
        ]
        for m in sample_matches:
            cache_match_result(m[0], m[1], m[2], m[3], m[4])

def get_rolling_league_averages(league_name):
    conn = sqlite3.connect('football_cache.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT home_goals, away_goals FROM matches WHERE league = ?
    ''', (league_name,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return 1.45, 1.15  # Default fallback baseline
        
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

def evaluate_match():
    print("\n========================================")
    print("      FOOTBALL LIVE xG ENGINE           ")
    print("========================================")
    
    league = input("Enter League Name (e.g., EPL): ") or "EPL"
    home = input("Enter Home Team: ") or "Home Team"
    away = input("Enter Away Team: ") or "Away Team"
    
    try:
        pre_home_xg = float(input("Enter Pre-Match Home xG baseline (default 1.50): ") or 1.50)
        pre_away_xg = float(input("Enter Pre-Match Away xG baseline (default 1.10): ") or 1.10)
        elapsed = int(input("Enter Elapsed Minutes (0 to 90): ") or 0)
        curr_home = int(input("Current Home Goals: ") or 0)
        curr_away = int(input("Current Away Goals: ") or 0)
    except ValueError:
        print("Invalid input format. Using standard defaults.")
        pre_home_xg, pre_away_xg, elapsed, curr_home, curr_away = 1.50, 1.10, 0, 0, 0

    league_home_avg, league_away_avg = get_rolling_league_averages(league)
    
    remaining_fraction = max(0.0, (90 - elapsed) / 90.0)
    remaining_home_xg = pre_home_xg * remaining_fraction
    remaining_away_xg = pre_away_xg * remaining_fraction
    
    print(f"\n--- ANALYSIS FOR: {home} vs {away} ---")
    print(f"Match State: {elapsed}' played | Score: {curr_home} - {curr_away}")
    print(f"Auto-Fetched League Baselines -> Home Avg: {league_home_avg} | Away Avg: {league_away_avg}")
    print(f"Projected Remaining xG -> Home: {remaining_home_xg:.2f} | Away: {remaining_away_xg:.2f}")
    
    h_no_goal = poisson_probability(remaining_home_xg, 0)
    a_no_goal = poisson_probability(remaining_away_xg, 0)
    
    print(f"\n[Poisson Probabilities for Rest of Match]")
    print(f"-> Home team scores 0 more goals: {h_no_goal * 100:.1f}%")
    print(f"-> Away team scores 0 more goals: {a_no_goal * 100:.1f}%")
    print("========================================\n")


if __name__ == "__main__":
    init_db()
    seed_initial_data()
    
    # Run interactive session
    while True:
        evaluate_match()
        cont = input("Evaluate another match? (y/n): ").strip().lower()
        if cont != 'y':
            print("Engine closed. Good luck with your punting today!")
            break
