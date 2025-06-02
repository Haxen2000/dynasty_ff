import os
import pandas as pd
import requests
from datetime import datetime

def fetch_all_players():
    url = "https://api.sleeper.app/v1/players/nfl"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def enrich_player_pool():
    # Set project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(project_root, "data", "league_data")

    # Load Sleeper rostered players
    rosters_df = pd.read_csv(os.path.join(data_path, "rosters.csv"))
    rosters_df["Sleeper_Player_ID"] = rosters_df["Sleeper_Player_ID"].astype(str)

    # Fetch full player metadata
    player_data = fetch_all_players()
    rows = []
    for pid, p in player_data.items():
        if not p.get("position") or p.get("status") == "practice squad":
            continue
        rows.append({
            "Sleeper_Player_ID": pid,
            "Full_Name": p.get("full_name"),
            "Position": p.get("position"),
            "Status": p.get("status"),
            "NFL_Team": p.get("team") or "FA",
            "years_exp": p.get("years_exp", 0),
            "rookie_year": (p.get("metadata") or {}).get("rookie_year", 0),
            "Birth_Date": p.get("birth_date")
        })

    all_players_df = pd.DataFrame(rows)
    all_players_df["Sleeper_Player_ID"] = all_players_df["Sleeper_Player_ID"].astype(str)
    # Merge to find rostered players
    merged = all_players_df.merge(
        rosters_df[["Sleeper_Player_ID", "Team"]],
        on="Sleeper_Player_ID",
        how="left"
    )
    merged["Team"] = merged["Team"].fillna("FA")

    # Load fantasy scores to identify active players
    fantasy_path = os.path.join(project_root, "data", "historical_stats", "fantasy_scores_2000_2024.csv")
    fantasy_df = pd.read_csv(fantasy_path)

    # Convert Birth_Date to datetime and compute Age
    today = pd.to_datetime(datetime.today().date())
    merged["Birth_Date"] = pd.to_datetime(merged["Birth_Date"], errors="coerce")
    merged["Age"] = ((today - merged["Birth_Date"]).dt.days / 365.25).round(1)

    # Restrict to last 2 seasons
    recent_years = [2023, 2024]
    recent_fantasy = fantasy_df[
        fantasy_df["Year"].isin(recent_years) & (fantasy_df["Fantasy_Pts"] > 0)
    ].copy()

    # Build a set of name-position keys from fantasy stats
    recent_fantasy["Key"] = recent_fantasy["Player"].str.lower().str.strip() + "|" + recent_fantasy["FantPos"]

    # Same key in merged player pool
    merged["Key"] = merged["Full_Name"].str.lower().str.strip() + "|" + merged["Position"]
    recent_keys = set(recent_fantasy["Key"])

    # Keep players who are either rookies or appeared in recent seasons
    merged["Rookie_Year"] = pd.to_numeric(merged["rookie_year"], errors="coerce")
    merged["Is_Rookie"] = (
        (merged["years_exp"].fillna(0).astype(int) == 0) &
        (merged["Age"] < 26)
    )
    merged["Had_Recent_Stats"] = merged["Key"].isin(recent_keys)

    # Final filter: keep if they’re rookies OR have recent stats
    merged = merged[merged["Is_Rookie"] | merged["Had_Recent_Stats"]]

    # Add flag columns
    merged["Is_Rostered"] = merged["Team"] != "FA"

    # Save output
    out_path = os.path.join(data_path, "player_pool_enriched.csv")
    merged.to_csv(out_path, index=False)
    print(f"✅ Saved full enriched player pool to {out_path}")

if __name__ == "__main__":
    enrich_player_pool()
