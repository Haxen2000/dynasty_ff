import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import StringIO

def scrape_draft_data():
  start_year = 2000
  end_year = 2025
  all_drafts = []  

  def flatten_columns(df):
    # Use second-level header if top-level is 'Unnamed'
    df.columns = [
        col[1] if "Unnamed" in col[0] else f"{col[0]}_{col[1]}"
        for col in df.columns.values
    ]
    return df

  # Parse each year's draft table
  for year in range(start_year, end_year + 1):
      url = f"https://www.pro-football-reference.com/years/{year}/draft.htm"
      res = requests.get(url)
      soup = BeautifulSoup(res.content, "html.parser")
      table = soup.find("table", {"id": "drafts"})

      if not table:
          continue

      df = pd.read_html(StringIO(str(table)))[0]
      df = flatten_columns(df)
      if 'Rnd' in df.columns:
        df = df[df["Rnd"] != "Rnd"]  # Remove repeated headers
      df["Draft_Year"] = year
      df = df.rename(columns={
          "Player": "Full_Name",
          "Pos": "Position",
          "Tm": "NFL_Team",
          "College/Univ": "College",
          "Pick": "Overall_Pick",
          "Rnd": "Draft_Round"
      })

      all_drafts.append(df[["Full_Name", "Position", "Draft_Year", "Draft_Round", "Overall_Pick", "NFL_Team", "College"]])

  # Combine and clean
  draft_df = pd.concat(all_drafts, ignore_index=True)
  draft_df["Draft_Round"] = pd.to_numeric(draft_df["Draft_Round"], errors="coerce")
  draft_df["Overall_Pick"] = pd.to_numeric(draft_df["Overall_Pick"], errors="coerce")

  # Save to CSV
  draft_df.to_csv("../data/historical_stats/rookie_draft_data.csv", index=False)
  print("✅ Saved to data/historical_stats/rookie_draft_data.csv")