import os
import pandas as pd
import numpy as np
from numpy.polynomial.polynomial import Polynomial

def generate_aging_curve_coefficients():
    # Define root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Load historical fantasy scores
    fantasy_path = os.path.join(project_root, "data", "historical_stats", "fantasy_scores_2000_2024.csv")
    df = pd.read_csv(fantasy_path)

    # Filter positions and clean
    df = df[df["FantPos"].isin(["QB", "RB", "WR", "TE"])]
    df = df.dropna(subset=["Player", "Age", "Year", "Fantasy_Pts"])
    df["Age"] = df["Age"].astype(int)
    df["PosRank"] = df.groupby(["Year", "FantPos"])["Fantasy_Pts"].rank(method="min", ascending=False)

    # Tiering function
    def get_tier(pos, rank):
        if pos == "QB":
            if rank <= 5:
                return "Top 5"
            elif rank <= 10:
                return "Top 10"
            elif rank <= 20:
                return "Top 20"
            elif rank <= 30:
                return "Top 30"
            else:
                return "Bench"

        elif pos == "RB":
            if rank <= 5:
                return "Top 5"
            elif rank <= 10:
                return "Top 10"
            elif rank <= 20:
                return "Top 20"
            elif rank <= 30:
                return "Top 30"
            elif rank <= 40:
                return "Top 40"
            elif rank <= 50:
                return "Top 50"
            else:
                return "Bench"

        elif pos == "WR":
            if rank <= 5:
                return "Top 5"
            elif rank <= 10:
                return "Top 10"
            elif rank <= 20:
                return "Top 20"
            elif rank <= 30:
                return "Top 30"
            elif rank <= 40:
                return "Top 40"
            elif rank <= 50:
                return "Top 50"
            elif rank <= 60:
                return "Top 60"
            elif rank <= 70:
                return "Top 70"
            else:
                return "Bench"

        elif pos == "TE":
            if rank <= 5:
                return "Top 5"
            elif rank <= 10:
                return "Top 10"
            elif rank <= 20:
                return "Top 20"
            elif rank <= 30:
                return "Top 30"
            else:
                return "Bench"


    df["Tier"] = df.apply(lambda row: get_tier(row["FantPos"], row["PosRank"]), axis=1)

    # Group by Age + Tier + Position
    # agg = df[df["Tier"] != "Bench"].groupby(["FantPos", "Tier", "Age"])["Fantasy_Pts"].mean().reset_index()
    agg = df.groupby(["FantPos", "Tier", "Age"])["Fantasy_Pts"].mean().reset_index()

    # Fit aging curve for each group
    rows = []
    position_tiers = {
        "QB":  ["Top 5", "Top 10", "Top 20", "Top 30", "Bench"],
        "RB":  ["Top 5", "Top 10", "Top 20", "Top 30", "Top 40", "Top 50", "Bench"],
        "WR":  ["Top 5", "Top 10", "Top 20", "Top 30", "Top 40", "Top 50", "Top 60", "Top 70", "Bench"],
        "TE":  ["Top 5", "Top 10", "Top 20", "Top 30", "Bench"]
    }

    for pos, tiers in position_tiers.items():
        for tier in tiers:
            subset = agg[(agg["FantPos"] == pos) & (agg["Tier"] == tier)]
            if subset.shape[0] < 5:
                continue

            x = subset["Age"]
            y = subset["Fantasy_Pts"]
            coefs = Polynomial.fit(x, y, 2).convert().coef
            a, b, c = coefs

            min_age = int(x.min())
            max_age = int(x.max())

            rows.append({
                "Position": pos,
                "Tier": tier,
                "a": round(a, 4),
                "b": round(b, 4),
                "c": round(c, 4),
                "min_age": min_age,
                "max_age": max_age
            })

    # Save output
    output = pd.DataFrame(rows)
    out_path = os.path.join(project_root, "data", "league_data", "aging_curve_coefficients.csv")
    output.to_csv(out_path, index=False)
    print(f"✅ Saved aging curve formulas to {out_path}")

if __name__ == "__main__":
    generate_aging_curve_coefficients()
