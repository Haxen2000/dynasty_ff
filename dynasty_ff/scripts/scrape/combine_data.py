import os
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
import random
from io import StringIO

def scrape_combine_data(start_year=2000, end_year=2025, save_path="../data/historical_stats/combine_results.csv"):
    all_data = []

    for year in range(start_year, end_year + 1):
        url = f"https://www.pro-football-reference.com/draft/{year}-combine.htm"
        print(f"Scraping {url}")
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to fetch {year}, status code: {response.status_code}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", id="combine")
        if table is None:
            print(f"No table found for {year}")
            continue

        # Parse table manually to extract player data and college links
        rows = table.find("tbody").find_all("tr")
        year_data = []

        for row in rows:
            if row.get("class") == ["thead"]:
                continue  # Skip extra header rows

            cols = row.find_all(["th", "td"])
            player_link = cols[0].find("a")
            player_name = player_link.text if player_link else cols[0].text.strip()
            position = cols[1].text.strip()
            school = cols[2].text.strip()

            college_link_tag = cols[3].find("a")
            college_stats_url = college_link_tag["href"] if college_link_tag else None
            college_stats_url = f"{college_stats_url}" if college_stats_url else None

            row_data = {
                "Full_Name": player_name,
                "Position": position,
                "College": school,
                "College_Stats_URL": college_stats_url,
                "Height": cols[4].text.strip(),
                "Weight": cols[5].text.strip(),
                "Forty_Yard": cols[6].text.strip(),
                "Vertical": cols[7].text.strip(),
                "Bench_Reps": cols[8].text.strip(),
                "Broad_Jump": cols[9].text.strip(),
                "Three_Cone": cols[10].text.strip(),
                "Shuttle": cols[11].text.strip(),
                "Draft_Info": cols[12].text.strip(),
                "Draft_Year": year
            }

            year_data.append(row_data)

        df = pd.DataFrame(year_data)

        # Drop repeated header rows
        df = df[df["Full_Name"] != "Player"]

        all_data.append(df)

        # Rate limiting
        time.sleep(random.uniform(15, 45))

    if not all_data:
        print("No data scraped.")
        return

    full_df = pd.concat(all_data, ignore_index=True)

    # Clean up data types
    for col in ["Weight", "Forty_Yard", "Vertical", "Bench_Reps", "Broad_Jump", "Three_Cone", "Shuttle"]:
        full_df[col] = pd.to_numeric(full_df[col], errors="coerce")

    full_df.to_csv(save_path, index=False)
    print(f"Saved {len(full_df)} rows to {save_path}")
