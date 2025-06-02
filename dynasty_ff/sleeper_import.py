import os
import json
import pandas as pd
from sleeper_wrapper import League

def get_roster_dataframe(league_id: str) -> pd.DataFrame:
    league = League(league_id)
    rosters = league.get_rosters()
    users = league.get_users()
    user_map = {user["user_id"]: user.get("display_name", "Unknown") for user in users}

    rows = []
    for r in rosters:
        owner_name = user_map.get(r.get("owner_id"), "Unknown")
        for pid in r.get("players", []):
            rows.append({
                "Team": owner_name,
                "Sleeper_Player_ID": pid,
                "Roster_ID": r.get("roster_id"),
                "Notes": "Rostered"
            })

    return pd.DataFrame(rows)

def get_league_settings(league_id: str) -> dict:
    league = League(league_id)
    return league.get_league()

def save_rosters_and_settings(league_id: str):
    # Dynamically set save path to project_root/data/league_data
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    save_dir = os.path.join(project_root, "data", "league_data")
    os.makedirs(save_dir, exist_ok=True)

    df = get_roster_dataframe(league_id)
    df.to_csv(os.path.join(save_dir, "rosters.csv"), index=False)
    print(f"✅ Saved rosters.csv to {save_dir}")

    settings = get_league_settings(league_id)
    with open(os.path.join(save_dir, "scoring_raw.json"), "w") as f:
        json.dump(settings, f, indent=2)
    print(f"✅ Saved scoring_raw.json to {save_dir}")
