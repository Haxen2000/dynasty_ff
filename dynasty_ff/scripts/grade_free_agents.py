import os
import pandas as pd

def grade_free_agents(top_n=100, pos=None, mode="all"):
    """
    Grades unrostered players by projected value.

    Args:
        top_n (int): number of players to include in top list
        pos (str or None): filter by position (e.g., 'QB', 'WR'), or None for all
        mode (str): 'all', 'rookies', or 'vets'
    """

    # Load data
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    df = pd.read_csv(os.path.join(project_root, "data", "league_data", "dynasty_projections.csv"))

    # Filter to unrostered
    df = df[df["Rostered"] == 0]

    # Apply mode filter
    if mode == "rookies":
        df = df[df["Rookie"] == 1]
    elif mode == "vets":
        df = df[df["Rookie"] == 0]

    # Apply position filter
    if pos:
        df = df[df["Position"] == pos.upper()]

    # Rank and trim# Define custom tier order
    tier_order = {"A": 0, "B": 1, "C": 2, "Flex": 3, "Bench": 4}

    # Add a helper column for sorting
    df["Tier_Sort"] = df["Tier"].map(tier_order)

    # Sort by Tier first (ascending = A first), then by Proj_Career (descending)
    top_df = df.sort_values(["Tier_Sort", "Proj_Career"], ascending=[True, False]).head(top_n)

    # Drop unnecessary columns for cleaner display
    columns_to_drop = ["Tier_Sort", "Sleeper_Player_ID", "Rostered", "Rookie", "Rookie_Year", "Draft_Round", "Overall_Pick"]
    top_df = top_df.drop(columns=columns_to_drop)

    # Save output
    suffix = f"{mode}_{pos.upper() if pos else 'all'}"
    output_path = os.path.join(project_root, "data", "league_data", f"top_unrostered_{suffix}.csv")
    top_df.to_csv(output_path, index=False)
    print(f"✅ Saved {len(top_df)} players to {output_path}")

    return top_df

# Example usage
if __name__ == "__main__":
    grade_free_agents(top_n=50, pos="WR", mode="rookies")  # Top 50 rookie WRs
