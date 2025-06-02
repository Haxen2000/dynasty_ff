import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from io import StringIO

POSITION_SUFFIX = {
    "QB": "passing",
    "RB": "rushing",
    "WR": "receiving"
}

# Dynamically resolve project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(project_root, "data", "historical_stats")
os.makedirs(data_dir, exist_ok=True)

def scrape_position_stats(start_year=2000, end_year=2024, position="QB"):
    if position not in POSITION_SUFFIX:
        raise ValueError("Supported positions: QB, RB, WR")

    suffix = POSITION_SUFFIX[position]
    all_data = []

    for year in range(start_year, end_year + 1):
        url = f"https://www.pro-football-reference.com/years/{year}/{suffix}.htm"
        print(f"Fetching {position} stats for {year}...")
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        table = soup.find("table")

        if table is None:
            print(f"No data found for {year} - skipping.")
            continue
        else:
            print("Found table at URL: " + url)
        
        df = pd.read_html(StringIO(str(table)))[0]

        # Drop any rows where 'Player' is actually the column header again
        if 'Player' in df.columns:
            df = df[df['Player'] != 'Player']

        # Add year and position for context
        df["Year"] = year
        df["Position"] = position

        all_data.append(df)
        time.sleep(1.5)  # Be respectful to PFR

    if not all_data:
        return pd.DataFrame()

    combined = pd.concat(all_data, ignore_index=True)

    # Convert numeric columns
    for col in combined.columns:
        try:
            combined[col] = pd.to_numeric(combined[col])
        except:
            pass  # Keep text columns as-is

    return combined


def scrape_all_positions(start_year=2000, end_year=2024):
    for position in ["QB", "RB", "WR"]:
        df = scrape_position_stats(start_year, end_year, position)
        if not df.empty:
            filepath = os.path.join(data_dir, f"{position.lower()}_{start_year}_{end_year}.csv")
            df.to_csv(filepath, index=False)
            print(f"Saved {position} data to {filepath}")
        else:
            print(f"No data for {position} - skipping save.")


if __name__ == "__main__":
    scrape_all_positions(start_year=2000, end_year=2024)
