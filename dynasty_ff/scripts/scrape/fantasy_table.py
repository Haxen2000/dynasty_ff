import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from io import StringIO

def flatten_columns(df):
    # Use second-level header if top-level is 'Unnamed'
    df.columns = [
        col[1] if "Unnamed" in col[0] else f"{col[0]}_{col[1]}"
        for col in df.columns.values
    ]
    return df

def scrape_fantasy_table(start_year=2000, end_year=2024):
    all_data = []

    for year in range(start_year, end_year + 1):
        url = f"https://www.pro-football-reference.com/years/{year}/fantasy.htm"
        print(f"🔄 Fetching fantasy stats for {year}...")
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        table = soup.find("table")

        if table is None:
            print(f"❌ Table not found for {year}")
            continue

        # Read multi-level headers
        df = pd.read_html(StringIO(str(table)), header=[0, 1])[0]
        df = flatten_columns(df)

        # Identify the true Player column
        player_col = next(col for col in df.columns if col.endswith("_Player") or col == "Player")

        # Drop repeated header rows from the table body
        df = df[df[player_col].notna()]
        df = df[df[player_col] != "Player"]

        # Standardize player column name
        df.rename(columns={player_col: "Player"}, inplace=True)
        # Standardize player names (remove *, +)
        df["Player"] = df["Player"].str.replace(r"[*+]", "", regex=True).str.strip()

        # Add year for context
        df["Year"] = year
        all_data.append(df)
        time.sleep(1.5)

    return pd.concat(all_data, ignore_index=True)

def save_fantasy_history():
    df = scrape_fantasy_table()
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(project_root, "data", "historical_stats", "fantasy_history_2000_2024.csv")
    df.to_csv(path, index=False)
    print(f"✅ Saved fantasy history to {path}")
