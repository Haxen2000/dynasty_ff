import os
import pandas as pd
from parse_scoring import load_scoring_rules

def load_fantasy_history(start_year=2010):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(project_root, "data", "historical_stats", "fantasy_history_2000_2024.csv")
    df = pd.read_csv(path)
    df = df[df["Year"] >= start_year]
    return df

def calculate_fantasy_points_from_flat_columns(df, weights):
    df = df.copy()

    # List of all scoring-relevant columns we expect
    numeric_cols = [
        "Passing_Yds", "Passing_TD", "Passing_Int",
        "Rushing_Yds", "Rushing_TD",
        "Receiving_Rec", "Receiving_Yds", "Receiving_TD",
        "Fumbles_FL", "Scoring_2PM", "Scoring_2PP"
    ]

    # Make sure all columns exist and are numeric with NaNs filled as 0
    for col in numeric_cols:
        df[col] = pd.to_numeric(df.get(col, 0), errors="coerce").fillna(0)

    # Final fantasy point formula
    df["Fantasy_Pts"] = (
        df["Passing_Yds"] * weights.get("pass_yd", 0) +
        df["Passing_TD"] * weights.get("pass_td", 0) +
        df["Passing_Int"] * weights.get("pass_int", 0) +

        df["Rushing_Yds"] * weights.get("rush_yd", 0) +
        df["Rushing_TD"] * weights.get("rush_td", 0) +

        df["Receiving_Rec"] * weights.get("rec", 0) +
        df["Receiving_Yds"] * weights.get("rec_yd", 0) +
        df["Receiving_TD"] * weights.get("rec_td", 0) +

        df["Scoring_2PM"] * 2 +
        df["Scoring_2PP"] * 2 +

        df["Fumbles_FL"] * weights.get("fum_lost", 0)
    )
    return df

def save_fantasy_scores(df):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_path = os.path.join(project_root, "data", "historical_stats", "fantasy_scores_2000_2024.csv")
    df.to_csv(out_path, index=False)
    print(f"✅ Saved fantasy points to {out_path}")

def run_fantasy_score_pipeline():
    weights = load_scoring_rules()
    df = load_fantasy_history()
    df_fp = calculate_fantasy_points_from_flat_columns(df, weights)
    save_fantasy_scores(df_fp)
