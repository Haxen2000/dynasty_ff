import os
import pandas as pd
from sleeper_wrapper import Players

def load_rostered_ids():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(project_root, "data", "league_data", "player_pool_enriched.csv")
    df = pd.read_csv(path)
    return set(df["Sleeper_Player_ID"].astype(str))

def classify_player(p, rostered_ids):
    pid = p.get("player_id")
    status = (p.get("status") or "").lower()
    position = p.get("position")
    years_exp = p.get("years_exp", 0)
    team = p.get("team")

    if pid in rostered_ids:
        return "Rostered"

    if position not in {"QB", "RB", "WR", "TE"}:
        return "Ignore"

    if status == "practice squad":
        return "Ignore"

    active_statuses = {
        "active", "inactive", "injured reserve",
        "non football injury", "physically unable to perform"
    }

    if status in active_statuses:
        return "Free Agent"

    if team is None and years_exp == 0:
        return "Rookie"

    return "Retired"

def build_classified_pool():
    players = Players().get_all_players()
    rostered_ids = load_rostered_ids()

    rows = []
    for p in players.values():
        full_name = p.get("full_name", "").strip()
        if not full_name:
            continue

        player_id = p.get("player_id")
        position = p.get("position")
        team = p.get("team")
        status = p.get("status")
        rookie_year = (p.get("metadata") or {}).get("rookie_year", 0)
        years_exp = p.get("years_exp", 0)
        is_rookie = int(years_exp == 0)

        classification = classify_player(p, rostered_ids)

        if classification == "Ignore":
            continue

        rows.append({
            "Sleeper_Player_ID": player_id,
            "Full_Name": full_name,
            "Position": position,
            "Team": team,
            "Status": status,
            "Years_Exp": years_exp,
            "Rookie_Year": rookie_year,
            "Is_Rookie": is_rookie,
            "Dynasty_Status": classification
        })

    df = pd.DataFrame(rows)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_path = os.path.join(project_root, "data", "league_data", "player_statuses.csv")
    df.to_csv(out_path, index=False)
    print(f"✅ Saved classified player pool to {out_path}")
