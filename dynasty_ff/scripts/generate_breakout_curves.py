import os
import pandas as pd

def generate_breakout_data():
    # Set paths
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(project_root, "data", "historical_stats")
    out_path = os.path.join(project_root, "data", "league_data")
    os.makedirs(out_path, exist_ok=True)

    # Load fantasy scores
    fantasy_df = pd.read_csv(os.path.join(data_path, "fantasy_scores_2000_2024.csv"))
    fantasy_df = fantasy_df[fantasy_df["FantPos"].isin(["QB", "RB", "WR", "TE"])]
    fantasy_df = fantasy_df.dropna(subset=["Age", "Fantasy_Pts"])
    fantasy_df["Age"] = fantasy_df["Age"].astype(int)

    # Define tier cutoffs per position
    tier_cutoffs = {
        "QB": [5, 10, 20, 30],
        "RB": [5, 10, 20, 30],
        "WR": [5, 10, 20, 30],
        "TE": [5, 10, 20, 30]
    }

    all_breakouts = []

    for pos, cutoffs in tier_cutoffs.items():
        pos_df = fantasy_df[fantasy_df["FantPos"] == pos].copy()
        pos_df["Tier"] = pos_df["Fantasy_PosRank"].apply(lambda r: next(
            (f"Top {cut}" for cut in cutoffs if r <= cut), "Bench"
        ))

        avg_by_age = (
            pos_df.groupby(["Age", "Tier"])["Fantasy_Pts"]
            .mean()
            .reset_index()
        )
        avg_by_age["Position"] = pos
        all_breakouts.append(avg_by_age)

    result_df = pd.concat(all_breakouts, ignore_index=True)
    result_df = result_df.rename(columns={"Fantasy_Pts": "Avg_Fantasy_Pts"})

    # Save output
    result_df.to_csv(os.path.join(out_path, "breakout_probabilities.csv"), index=False)
    print(f"✅ Breakout probabilities saved to {out_path}/breakout_probabilities.csv")

if __name__ == "__main__":
    generate_breakout_data()
