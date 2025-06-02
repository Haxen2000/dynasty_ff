import os
import json

def load_scoring_rules():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scoring_path = os.path.join(project_root, "data", "league_data", "scoring_raw.json")

    with open(scoring_path, "r") as f:
        raw = json.load(f)

    raw_scoring = raw.get("scoring_settings", {})

    # Use values as-is — Sleeper already gives them as per-yard or per-event points
    scoring_weights = {
        "pass_yd": raw_scoring.get("pass_yd", 0.04),    # 1 pt per 25 yds → 0.04
        "pass_td": raw_scoring.get("pass_td", 4),
        "pass_int": raw_scoring.get("pass_int", -1),

        "rush_yd": raw_scoring.get("rush_yd", 0.1),
        "rush_td": raw_scoring.get("rush_td", 6),

        "rec": raw_scoring.get("rec", 1),               # full PPR
        "rec_yd": raw_scoring.get("rec_yd", 0.1),
        "rec_td": raw_scoring.get("rec_td", 6),

        "fum_lost": raw_scoring.get("fum_lost", -2)
    }

    return scoring_weights
