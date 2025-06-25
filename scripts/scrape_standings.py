# -*- coding: utf-8 -*-
"""
@author: peterpiperpickedpeppers
Description: Scrapes tournament standings from MTGMelee.
"""

# set up workspace
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.selenium_helpers import wait_for_element, scroll_page, accept_cookies
from utils.data_utils import save_df, clean_player_name
import pandas as pd
from globals import CONFIG
import os

def run_standings_scraper():
    """Scrapes tournament standings from the mtgmelee website."""
    print("Scraping standings.. .")

    # one time variables
    filePath = os.path.join(CONFIG.data_folder, f"{CONFIG.eventName} standings.csv")
    
    # get browser instance from globals
    driver = CONFIG.browser_instance
    sleep(3)
    
    # accept cookies
    accept_cookies(driver)
    sleep(3)
    
    # scroll down a bit to show standings
    scroll_page(driver, pixels=900)
    sleep(3)
    
    table_data = []
    
    while True:
        wait_for_element(driver, "//table[@id='tournament-standings-table']//tr")
        
        # Extract rows again after each page change
        rows = driver.find_elements(By.XPATH, "//table[@id='tournament-standings-table']//tr")
    
        for row in rows:
            # Extract all columns inside the row
            columns = row.find_elements(By.TAG_NAME, "td")
    
            if len(columns) >= 3:  # Ensure there is a Decklists column
                # extract deck ID and decklist
                try:
                    deck_link = columns[2].find_element(By.TAG_NAME, "a")  # 3rd column is decklist
                    deck_id = deck_link.get_attribute("data-id")
                    deck_name = deck_link.text.strip()
                except:
                    deck_id = None
                    deck_name = None
    
                # Store extracted data
                table_data.append({
                    "rank": columns[0].text.strip(),
                    "player": columns[1].text.strip(),
                    "deck id": deck_id,
                    "deck name": deck_name,
                    "match record": columns[3].text.strip(),
                    "game record": columns[4].text.strip(),
                    "points": columns[5].text.strip()
                })
    
        print(f"Extracted {len(rows)} rows from current page")
    
        # Try to click 'Next' button if available
        try:
            next_button = wait_for_element(driver, '//*[@id="tournament-standings-table_next"]')
            next_button.click()
            print("NEXT PAGE")
    
            # Wait for new table data to load before proceeding
            WebDriverWait(driver, 5).until(
                EC.staleness_of(rows[0])
            )
    
        except:
            break
    
    # create dataframe and clean it
    df = pd.DataFrame(table_data)
    df["player"] = df["player"].apply(clean_player_name)
    df[['wins', 'losses', 'draws']] = df['match record'].str.split("-", expand=True)
    
    # save dataframe
    save_df(df, filePath)
    
    print("Standings scraped.")
