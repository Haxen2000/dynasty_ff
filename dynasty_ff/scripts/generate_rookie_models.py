import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from sklearn.linear_model import LinearRegression

def generate_rookie_models():
    # === Load rookie draft and projection data ===
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(project_root, "data", "league_data")
    output_path = os.path.join(data_path, "rookie_curves")
    os.makedirs(output_path, exist_ok=True)

    proj_df = pd.read_csv(os.path.join(data_path, "dynasty_projections.csv"))

    # Focus on rookies with valid pick data
    rookies_df = proj_df[(proj_df["Rookie"] == 1) & (proj_df["Overall_Pick"].notna())].copy()

    # Initialize models and output column
    position_models = {}
    proj_df["Expected_Proj_Career"] = np.nan

    # === Fit + plot for each position ===
    positions = ["QB", "RB", "WR", "TE"]
    for pos in positions:
        pos_df = rookies_df[rookies_df["Position"] == pos]
        if pos_df.empty:
            continue

        x = pos_df["Overall_Pick"]
        y = pos_df["Proj_Career"]
        X = x.values.reshape(-1, 1)

        # Linear Regression
        model = LinearRegression()
        model.fit(X, y)
        position_models[pos] = model

        # Predict for plotting
        x_range = np.linspace(x.min(), x.max(), 100)
        y_pred = model.predict(x_range.reshape(-1, 1))

        # Plot
        plt.figure(figsize=(8, 5))
        plt.scatter(x, y, alpha=0.6, label="Actual")
        plt.plot(x_range, y_pred, color='red', label=f"Fit: y = {model.coef_[0]:.2f}x + {model.intercept_:.2f}")
        plt.title(f"{pos} Rookie Career Projection vs Draft Pick")
        plt.xlabel("Overall Draft Pick")
        plt.ylabel("Projected Career Points")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(output_path, f"{pos}_rookie_curve.png"))
        plt.close()

        print(f"✅ Saved curve for {pos}: y = {model.coef_[0]:.2f}x + {model.intercept_:.2f}")

    # === Apply model predictions to all rookies ===
    for idx, row in proj_df.iterrows():
        if row["Rookie"] == 1 and pd.notna(row["Overall_Pick"]):
            pos = row["Position"]
            if pos in position_models:
                model = position_models[pos]
                expected = model.predict([[row["Overall_Pick"]]])[0]
                proj_df.at[idx, "Expected_Proj_Career"] = round(expected, 1)

    # Save updated projections
    output_csv = os.path.join(data_path, "dynasty_projections_adjusted.csv")
    proj_df.to_csv(output_csv, index=False)
    print(f"📁 Saved updated projections to: {output_csv}")

if __name__ == "__main__":
    generate_rookie_models()
