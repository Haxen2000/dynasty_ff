import sys
import os
import importlib
import scrape_all_pfr_stats

# Add the scripts directory to path so imports work
sys.path.append(os.path.dirname(__file__))

importlib.reload(scrape_all_pfr_stats)
from scrape_all_pfr_stats import scrape_all_positions

def fetch_all_data():
    print("Starting NFL data fetch...")
    scrape_all_positions(start_year=2000, end_year=2024)
    print("Data fetch complete.")

if __name__ == "__main__":
    fetch_all_data()
