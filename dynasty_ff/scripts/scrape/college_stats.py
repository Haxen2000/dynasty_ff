import pandas as pd
import os
import requests
from bs4 import BeautifulSoup
import time
import random
from tqdm import tqdm
from io import StringIO

def scrape_college_stats():
    combine_csv = "../data/historical_stats/combine_results.csv"
    out_csv = "../data/historical_stats/college_stats.csv"
    offensive_positions = ["QB", "RB", "WR", "TE"]

    table_ids = {
        "QB": ["passing_standard", "rushing_standard"],
        "RB": ["rushing_standard"],
        "WR": ["receiving_standard"],
        "TE": ["receiving_standard"]
    }

    combine_df = pd.read_csv(combine_csv)
    combine_df = combine_df[combine_df["Position"].isin(offensive_positions)]

    all_stats = []

    for _, row in tqdm(combine_df.iterrows(), total=len(combine_df), desc="Scraping college stats"):
        name = row["Full_Name"]
        position = row["Position"]
        college_url = row.get("College_Stats_URL")

        if pd.isna(college_url) or not isinstance(college_url, str) or "sports-reference.com" not in college_url:
            continue

        try:
            response = requests.get(college_url)
            if response.status_code != 200:
                print(f"Failed for {name}: {response.status_code}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            tables = []

            for tid in table_ids.get(position, []):
                table = soup.find("table", {"id": tid})
                if not table:
                    continue

                df = pd.read_html(StringIO(str(table)))[0]

                # Handle multi-index headers
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [
                        col[1] if "Unnamed" in col[0] else f"{col[0]}_{col[1]}"
                        for col in df.columns
                    ]
                else:
                    df.columns = df.columns.astype(str)

                # Clean rows: remove internal headers and career totals
                df = df[df[df.columns[0]] != df.columns[0]]
                df = df[df["Season"].notna() & (df["Season"] != "Career")]

                df["Full_Name"] = name
                df["Position"] = position
                tables.append(df)

            if tables:
                combined = pd.concat(tables, axis=1)
                combined = combined.loc[:, ~combined.columns.duplicated()]
                all_stats.append(combined)

            time.sleep(random.uniform(2.5, 4.5))

        except Exception as e:
            print(f"Error scraping {name}: {e}")

    if all_stats:
        final_df = pd.concat(all_stats, ignore_index=True)
        final_df.to_csv(out_csv, index=False)
        print(f"Saved college stats to {out_csv}")
    else:
        print("No stats collected.")
