import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# Fantasy-relevant positions only
PRODUCING_POSITIONS = {"QB", "RB", "WR", "TE"}

# NFL team codes used by ESPN URLs
NFL_TEAMS = {
    "BUF", "MIA", "NE", "NYJ", "BAL", "CIN", "CLE", "PIT",
    "HOU", "IND", "JAX", "TEN", "DEN", "KC", "LV", "LAC",
    "DAL", "NYG", "PHI", "WAS", "CHI", "DET", "GB", "MIN",
    "ATL", "CAR", "NO", "TB", "ARI", "LAR", "SF", "SEA"
}

def scrape_depth_chart(team_code):
    url = f"https://www.espn.com/nfl/team/depth/_/name/{team_code.lower()}"
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(url)
    time.sleep(2)  # Wait for JS to render
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    position_table = soup.select(".Table--fixed-left tbody tr")
    player_table = soup.select(".Table__Scroller table tbody tr")

    positions = [row.get_text(strip=True) for row in position_table]
    players = [[cell.get_text(strip=True) for cell in row.select("td")] for row in player_table]

    data = []
    for pos, player_row in zip(positions, players):
        base_pos = pos.split()[0]
        if base_pos in PRODUCING_POSITIONS:
            for i, player in enumerate(player_row):
                if player != "-":
                    data.append({
                        "NFL_Team": team_code,
                        "Position": base_pos,
                        "Depth": i + 1,
                        "Player": player
                    })
    return data

def scrape_all_depth_charts():
    all_data = []
    for team in sorted(NFL_TEAMS):
        print(f"Scraping: {team}")
        try:
            team_data = scrape_depth_chart(team)
            all_data.extend(team_data)
        except Exception as e:
            print(f"Failed to scrape {team}: {e}")
    df = pd.DataFrame(all_data)
    df.to_csv("../data/league_data/depth_charts.csv", index=False)
    print("Saved to depth_charts.csv")

if __name__ == "__main__":
    scrape_all_depth_charts()
