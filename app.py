import math
import sqlite3
import streamlit as st

# ==========================================
# 1. DATABASE & ROLLING AVERAGES ENGINE
# ==========================================


def init_db():
  conn = sqlite3.connect("football_cache.db")
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            league TEXT,
            home_team TEXT,
            away_team TEXT,
            home_goals INTEGER,
            away_goals INTEGER
        )
    """)
  conn.commit()
  conn.close()


def seed_initial_data():
  conn = sqlite3.connect("football_cache.db")
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
    ]
    for m in sample_matches:
      conn = sqlite3.connect("football_cache.db")
      cursor = conn.cursor()
      cursor.execute(
          """
            INSERT INTO matches (league, home_team, away_team, home_goals,"
            " away_goals)
            VALUES (?, ?, ?, ?, ?)
        """,
          (m[0], m[1], m[2], m[3], m[4]),
      )
      conn.commit()
      conn.close()


def get_rolling_league_averages(league_name):
  conn = sqlite3.connect("football_cache.db")
  cursor = conn.cursor()
  cursor.execute(
      """
        SELECT home_goals, away_goals FROM matches WHERE league = ?
    """,
      (league_name,),
  )
  rows = cursor.fetchall()
  conn.close()

  if not rows:
    return 1.45, 1.15

  total_matches = len(rows)
  total_home_goals = sum(row[0] for row in rows)
  total_away_goals = sum(row[1] for row in rows)

  return round(total_home_goals / total_matches, 2), round(
      total_away_goals / total_matches, 2
  )


# ==========================================
# 2. POISSON MATH
# ==========================================


def poisson_probability(lmbda, k):
  return (math.exp(-lmbda) * (lmbda ** k)) / math.factorial(k)


# ==========================================
# 3. STREAMLIT UI LAYOUT
# ==========================================

st.set_page_config(
    page_title="Market Rhythm Football Engine", page_icon="⚽", layout="centered"
)

init_db()
seed_initial_data()

st.title("⚽ Football Live xG & Probability Engine")
st.markdown("Real-time match tracking and probabilistic analysis dashboard.")

# Sidebar inputs for match configuration
st.sidebar.header("Match Parameters")
league = st.sidebar.text_input("League Name", "EPL")
home_team = st.sidebar.text_input("Home Team", "Arsenal")
away_team = st.sidebar.text_input("Away Team", "Chelsea")

pre_home_xg = st.sidebar.number_input(
    "Pre-Match Home xG Baseline", value=1.50, step=0.05
)
pre_away_xg = st.sidebar.number_input(
    "Pre-Match Away xG Baseline", value=1.10, step=0.05
)

elapsed = st.sidebar.slider("Elapsed Minutes", 0, 90, 60)
curr_home = st.sidebar.number_input(
    "Current Home Goals", min_value=0, value=1, step=1
)
curr_away = st.sidebar.number_input(
    "Current Away Goals", min_value=0, value=0, step=1
)

if st.button("Run Live Analysis", type="primary"):
  league_home_avg, league_away_avg = get_rolling_league_averages(league)

  remaining_fraction = max(0.0, (90 - elapsed) / 90.0)
  remaining_home_xg = pre_home_xg * remaining_fraction
  remaining_away_xg = pre_away_xg * remaining_fraction

  st.subheader(f"Match: {home_team} vs {away_team}")

  # Metric Display Cards
  col1, col2, col3 = st.columns(3)
  col1.metric("Elapsed Time", f"{elapsed}'")
  col2.metric("Current Score", f"{curr_home} - {curr_away}")
  col3.metric("League Averages", f"H: {league_home_avg} | A: {league_away_avg}")

  st.markdown("---")

  # xG Output
  st.write("### 📊 Projected Remaining xG")
  r_col1, r_col2 = st.columns(2)
  r_col1.metric(f"{home_team} (Remaining)", f"{remaining_home_xg:.2f}")
  r_col2.metric(f"{away_team} (Remaining)", f"{remaining_away_xg:.2f}")

  # Poisson Probabilities
  h_no_goal = poisson_probability(remaining_home_xg, 0)
  a_no_goal = poisson_probability(remaining_away_xg, 0)

  st.write("### 🎯 In-Play Probabilities")
  st.info(
      f"Probability **{home_team}** scores **0 more goals**: **{h_no_goal * 100:.1f}%**"
  )
  st.info(
      f"Probability **{away_team}** scores **0 more goals**: **{a_no_goal * 100:.1f}%**"
  )