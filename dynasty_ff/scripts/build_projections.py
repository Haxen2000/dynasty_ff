import os
import pandas as pd
import numpy as np

def build_dynasty_projections():
    current_year = 2025
    # Paths
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(project_root, "data", "league_data")
    roster_df = pd.read_csv(os.path.join(data_path, "player_pool_enriched.csv"))
    aging_df = pd.read_csv(os.path.join(data_path, "aging_curve_coefficients.csv"))
    fantasy_df = pd.read_csv(os.path.join(project_root, "data", "historical_stats", "fantasy_scores_2000_2024.csv"))
    rookie_df = pd.read_csv(os.path.join(data_path, "rookie_draft_data.csv"))

    # Load breakout probabilities if available
    breakout_path = os.path.join(data_path, "breakout_probabilities.csv")
    if os.path.exists(breakout_path):
        breakout_df = pd.read_csv(breakout_path)
    else:
        breakout_df = None

    # Clean + filter player pool
    roster_df = roster_df[roster_df["Status"].isin(["Active", "injured reserve", "non football injury", "physically unable to perform", None])]
    roster_df = roster_df[roster_df["Position"].isin(["QB", "RB", "WR", "TE"])]
    roster_df = roster_df.dropna(subset=["Age"])
    roster_df["Age"] = roster_df["Age"].astype(int)

    tier_labels = {
        "QB":  [(5, "Top 5"), (10, "Top 10"), (20, "Top 20"), (30, "Top 30")],
        "RB":  [(5, "Top 5"), (10, "Top 10"), (20, "Top 20"), (30, "Top 30"), (40, "Top 40"), (50, "Top 50")],
        "WR":  [(5, "Top 5"), (10, "Top 10"), (20, "Top 20"), (30, "Top 30"), (40, "Top 40"), (50, "Top 50"), (60, "Top 60"), (70, "Top 70")],
        "TE":  [(5, "Top 5"), (10, "Top 10"), (20, "Top 20"), (30, "Top 30")]
    }

    # Define maximum allowed tier by position
    max_tiers_by_pos = {
        "QB": 30,
        "RB": 50,
        "WR": 70,
        "TE": 30
    }

    projections = []
    for _, row in roster_df.iterrows():
        pos = row["Position"]
        age = int(row["Age"])
        player_id = row["Sleeper_Player_ID"]
        rookie_year = int(row["rookie_year"]) if pd.notnull(row["rookie_year"]) else 0
        is_rookie = int(row.get("Is_Rookie", False))
        is_sophomore = int(rookie_year == current_year - 1)
        is_rostered = int(row.get("Is_Rostered", False))
        full_name = row.get("Full_Name", "")
        team = row.get("Team")

        rookie_row = rookie_df[rookie_df["Full_Name"] == full_name]

        if not rookie_row.empty:
            print(f"Found rookie: {full_name}")
            draft_round = int(rookie_row["Draft_Round"].values[0])
            overall_pick = int(rookie_row["Overall_Pick"].values[0])
        else:
            draft_round = None
            overall_pick = None


        # Look up breakout probability
        breakout_row = breakout_df[
            (breakout_df["Position"] == pos) &
            (breakout_df["Age"] == age)
        ]

        breakout_prob = breakout_row["Avg_Fantasy_Pts"].values[0] if not breakout_row.empty else 0.0

        # Historical performance
        player_hist = fantasy_df[fantasy_df["Player"] == full_name]
        player_hist = player_hist[player_hist["FantPos"] == pos]
        player_hist = player_hist.sort_values("Year", ascending=False)

        past_scores = player_hist["Fantasy_Pts"].tolist()
        
        def assign_dynamic_tier(pos, most_recent_rank):
            tiers = tier_labels.get(pos)
            for top_n, label in tiers:
                if most_recent_rank <= top_n:
                    return label
            return "Bench"

        # Then apply:
        if not player_hist.empty:
            # Use average of up to last 3 seasons for tiering
            recent_ranks = player_hist["Fantasy_PosRank"].head(3)
            avg_rank = recent_ranks.mean()
            best_tier = assign_dynamic_tier(pos, avg_rank)

            if full_name == "Brandon Aiyuk":
                print(f"📊 Debug Brandon Aiyuk — Ranks: {recent_ranks.tolist()}, Avg Rank: {avg_rank}, Tier: {best_tier}")
        else:
            best_tier = f"Top {max_tiers_by_pos.get(pos, 70)}"


        # Use curve for position and best tier
        curve_row = aging_df[(aging_df["Position"] == pos) & (aging_df["Tier"] == best_tier)]
        if curve_row.empty:
            print(f"⚠️ Skipping {full_name} due to missing or invalid curve: {best_tier}")
            continue  # Skip if curve not found

        a, b, c = curve_row.iloc[0][["a", "b", "c"]]
        max_age = int(curve_row.iloc[0]["max_age"])

        def score_at_age(a, b, c, x):
            return a + b * x + c * (x ** 2)

        # Age-based curve scores
        future_scores = [score_at_age(a, b, c, age + i) for i in range(6)]
        future_scores = [s for i, s in enumerate(future_scores) if age + i <= max_age]
        # current_score = score_at_age(a, b, c, age)

        # Blended projections (weights can be tuned)
        historical_weight = 0.7
        curve_weight = 0.3

        def safe_mean(values):
            clean = [v for v in values if pd.notna(v)]
            return np.nanmean(clean) if clean else 0
        
        def weighted_recent_avg(scores, max_years):
            weights = [1.0, 0.75, 0.5, 0.35, 0.25][:max_years]
            values = scores[:max_years]
            return (
                sum(w * s for w, s in zip(weights, values) if pd.notna(s)) /
                sum(w for w, s in zip(weights, values) if pd.notna(s))
            ) if values else 0

        def blend_scores(hist_list, curve_list, years):
            hist_avg = weighted_recent_avg(hist_list, years)
            curve_avg = safe_mean(curve_list[:years]) if curve_list else 0
            return historical_weight * hist_avg + curve_weight * curve_avg

        # Tiering
        def get_value_tier(score, position):
            if position == "QB":
                if score >= 459.3:
                    return "A"
                elif score >= 394.4:
                    return "B"
                elif score >= 329.2:
                    return "C"
                elif score >= 225.3:
                    return "Flex"
                else:
                    return "Bench"

            elif position == "RB":
                if score >= 226.5:
                    return "A"
                elif score >= 185.7:
                    return "B"
                elif score >= 154.9:
                    return "C"
                elif score >= 99.7:
                    return "Flex"
                else:
                    return "Bench"

            elif position == "WR":
                if score >= 265.8:
                    return "A"
                elif score >= 187.5:
                    return "B"
                elif score >= 149.8:
                    return "C"
                elif score >= 104.2:
                    return "Flex"
                else:
                    return "Bench"

            elif position == "TE":
                if score >= 223.0:
                    return "A"
                elif score >= 163.0:
                    return "B"
                elif score >= 129.4:
                    return "C"
                elif score >= 81.2:
                    return "Flex"
                else:
                    return "Bench"

            else:
                return "Bench"  # fallback for unknown positions
        
        def flag_breakout_candidate(pos, age, tier, breakout_prob):
            if tier in ["Flex", "Bench"] and breakout_prob > 0.25:
                if pos == "WR" and 24 <= age <= 28:
                    return True 
                if pos == "RB" and 23 <= age <= 27:
                    return True
                if pos == "QB" and 25 <= age <= 30:
                    return True
                if pos == "TE" and 25 <= age <= 30:
                    return True
            return False

        if (is_rookie or is_sophomore) and len(past_scores) == 0:
            proj_1yr = future_scores[0] if future_scores else 0
            proj_3yr = safe_mean(future_scores[:3])
            proj_5yr = safe_mean(future_scores[:5])
        else:
            proj_1yr = blend_scores(past_scores, future_scores, 1)
            proj_3yr = blend_scores(past_scores, future_scores, 3)
            proj_5yr = blend_scores(past_scores, future_scores, 5)

        # Smarter career projection using curve window and player age
        min_age = int(age)
        start_age = max(min_age, age)
        end_age = min(max_age, age + 10)  # cap projection window to 10 years forward

        if start_age > end_age:
            career_scores = []
        else:
            career_scores = [score_at_age(a, b, c, a_val) for a_val in range(start_age, end_age + 1)]

        # Limit projections for older low-production veterans
        recent_scores = past_scores[:3]
        recent_total = sum([s for s in recent_scores if pd.notna(s)])
        limit_career = (
            is_rookie == 0 and is_sophomore == 0 and
            float(row.get("years_exp", 0)) > 2 and
            age > 26 and
            recent_total < 100
        )

        if full_name == "Josh Johnson":
            print("🧪 Debugging Josh Johnson")
            print(f"Is Rookie: {is_rookie}")
            print(f"Years Exp: {row.get('years_exp', 0)}")
            print(f"Age: {age}")
            print(f"Recent Total: {recent_total}")
            print(f"Career Scores: {career_scores}")

        if limit_career:
            print(f"⚠️ Limiting career projection for {full_name}: Age {age}, Exp {row.get('years_exp', 0)}, Recent Total {recent_total:.1f}")
            career_years = 1 if age >= max_age - 2 else 3
            proj_career = safe_mean(career_scores[:career_years])
        else:
            proj_career = safe_mean(career_scores)

        breakout_flag = flag_breakout_candidate(pos, age, get_value_tier(proj_career, pos), breakout_prob)

        if breakout_flag and proj_3yr > 0:
            proj_1yr *= 1.05
            proj_3yr *= 1.08
            proj_5yr *= 1.10
            proj_career *= 1.05

        if not is_rookie and not is_sophomore and row.get("years_exp", 0) > 5 and recent_total < 100:
            proj_career *= 0.75
            proj_3yr *= 0.85
            proj_5yr *= 0.85

        # Adjust projections for rookies/sophomores based on draft capital and lack of history
        if is_rookie or is_sophomore:
            if len(past_scores) == 0:
                if pd.notna(overall_pick):
                    overall_pick = float(overall_pick)
                    if overall_pick <= 32:
                        proj_career = safe_mean(future_scores[:6])
                    elif overall_pick <= 100:
                        proj_career = safe_mean(future_scores[:4])
                    elif overall_pick <= 224:
                        proj_career = safe_mean(future_scores[:2])
                    else:
                        proj_career = safe_mean(future_scores[:1])
                else:
                    # Undrafted with no history: very low projection
                    proj_career = 0.0
                    proj_1yr = 0.0
                    proj_3yr = 0.0
                    proj_5yr = 0.0

        # Raise floor for recent productive players
        productive_thresholds = {
            "QB": 20,
            "RB": 30,
            "WR": 40,
            "TE": 20
        }

        threshold = productive_thresholds.get(pos, 36)  # fallback to 36
        recent_ranks = player_hist["Fantasy_PosRank"].tolist()[:3]
        productive_years = sum(1 for r in recent_ranks if pd.notna(r) and r <= threshold)

        if productive_years >= 2:
            if proj_career < 100:
                proj_career = 100  # bump career floor
            if proj_1yr < 80:
                proj_1yr = 80  # bump near-term outlook

        projections.append({
            "Sleeper_Player_ID": player_id,
            "Player": full_name,
            "Position": pos,
            "Team": team,
            "NFL Team": row.get("NFL_Team") or "FA",
            "Age": age,
            "Rookie_Year": rookie_year,
            "Rookie": is_rookie,
            "Sophomore": is_sophomore,
            "Rostered": is_rostered,
            "Proj_1yr": round(proj_1yr, 1),
            "Proj_3yr": round(proj_3yr, 1),
            "Proj_5yr": round(proj_5yr, 1),
            "Proj_Career": round(proj_career, 1),
            "Tier": get_value_tier(proj_career, pos),
            "BreakoutProb": round(breakout_prob, 3),
            "BreakoutFlag": breakout_flag,
            "Draft_Round": draft_round,
            "Overall_Pick": overall_pick,
        })

    # Save
    proj_df = pd.DataFrame(projections)
    out_path = os.path.join(data_path, "dynasty_projections.csv")
    proj_df.to_csv(out_path, index=False)
    print(f"✅ Dynasty projections saved to {out_path}")

if __name__ == "__main__":
    build_dynasty_projections()
