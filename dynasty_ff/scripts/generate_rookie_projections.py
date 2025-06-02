import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

def generate_rookie_projections(max_years_exp=3):
    # Load core data
    pool_df = pd.read_csv("../data/league_data/player_pool_enriched.csv")
    proj_df = pd.read_csv("../data/league_data/dynasty_projections.csv")
    combine_df = pd.read_csv("../data/historical_stats/combine_results.csv")
    college_df = pd.read_csv("../data/historical_stats/college_stats.csv")

    # Merge in projection values (for training labels)
    proj_df = proj_df[["Player", "Proj_Career"]].rename(columns={"Player": "Full_Name"})
    df = pool_df.merge(proj_df, on="Full_Name", how="left")

    # Normalize name casing
    df["Full_Name"] = df["Full_Name"].str.lower().str.strip()
    combine_df["Full_Name"] = combine_df["Full_Name"].str.lower().str.strip()
    college_df["Full_Name"] = college_df["Full_Name"].str.lower().str.strip()

    # Merge in combine + college data
    df = df.merge(combine_df, on="Full_Name", how="left")
    df = df.merge(college_df, on="Full_Name", how="left")

    print(f"Total merged player rows: {len(df)}")
    print(f"Sample columns: {df.columns.tolist()}")

    results = []

    def parse_height(height_str):
        try:
            if isinstance(height_str, str):
                # Remove leading/trailing non-numeric characters like apostrophes or spaces
                height_str = height_str.strip().lstrip("'").strip()
                if '-' in height_str:
                    feet, inches = height_str.split('-')
                    return int(feet) * 12 + int(inches)
            return float(height_str) if height_str else None
        except:
            return None  # Return None for malformed or missing values

    for pos in ["QB", "RB", "WR", "TE"]:
        print(f"\n--- Processing position: {pos} ---")
        pos_df = df[df["Position"] == pos].copy()
        pos_df["Height"] = pos_df["Height"].apply(parse_height)

        # Define features and target
        possible_features = [
            # Combine metrics
            "Height", "Weight", "40yd", "Vertical", "Bench", "Broad Jump", "3Cone", "Shuttle",

            # Rushing stats
            "Rushing_Att", "Rushing_Yds", "Rushing_Y/A", "Rushing_TD", "Rushing_Y/G",

            # Receiving stats
            "Receiving_Rec", "Receiving_Yds", "Receiving_Y/R", "Receiving_TD", "Receiving_Y/G",

            # Passing stats (for QBs)
            "Cmp", "Att", "Cmp%", "Yds", "TD", "TD%", "Int", "Int%", "Y/A", "AY/A", "Y/C", "Y/G", "Rate"
        ]

        features = [f for f in possible_features if f in pos_df.columns and pos_df[f].notna().sum() > 0]
        print(f"Using {len(features)} features for {pos}: {features}")

        # Training set: must have a target
        train_df = pos_df[pos_df["Proj_Career"].notna()].dropna(subset=features)
        print(f"{len(train_df)} rows with training labels for {pos}")

        if len(train_df) < 10 or not features:
            print(f"Skipping {pos}: not enough training data")
            continue

        X_train = train_df[features]
        y_train = train_df["Proj_Career"]

        # Train model
        model = xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.1)
        model.fit(X_train, y_train)

        # Apply model to rookies/sophomores with missing projections
        predict_df = pos_df[(pos_df["years_exp"] <= max_years_exp)]
        predict_df = predict_df.dropna(subset=features)
        print(f"{len(predict_df)} rookies/sophs with data to predict for {pos}")

        if predict_df.empty:
            continue

        predict_df["Rookie_Proj_Career"] = model.predict(predict_df[features])
        results.append(predict_df[["Full_Name", "Position", "Rookie_Proj_Career"]])

    if results:
        final_df = pd.concat(results)
        final_df.to_csv("../data/league_data/projected_rookies.csv", index=False)
        print("✅ Saved rookie projections to ../data/league_data/projected_rookies.csv")
    else:
        print("⚠️ No rookie projections generated.")

# Example usage:
# generate_rookie_projections()
