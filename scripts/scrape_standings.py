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

# functions

def find_valid_standings_round(driver):
    try:
        # Find all round buttons inside the selector container
        round_buttons = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "#standings-round-selector-container button.round-selector")
            )
        )

        # Pull all round names and reverse to prioritize most recent
        round_names = [btn.text.strip() for btn in round_buttons if btn.text.strip()]
        round_names.reverse()

        for round_name in round_names:
            try:
                print(f"Trying {round_name}...")

                # Refetch button dynamically
                button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(), '{round_name}')]"))
                )

                # Store current active round to confirm it changes
                try:
                    active_round = driver.find_element(By.CSS_SELECTOR, "#standings-round-selector-container .round-selector.active").text.strip()
                except:
                    active_round = None

                button.click()

                # Wait for the active round to update
                WebDriverWait(driver, 5).until(
                    lambda d: d.find_element(By.CSS_SELECTOR, "#standings-round-selector-container .round-selector.active").text.strip() != active_round
                )

                # Wait for table rows to appear
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
                )

                # Check number of rows
                tbody = driver.find_element(By.CSS_SELECTOR, "table tbody")
                rows = tbody.find_elements(By.TAG_NAME, "tr")

                if len(rows) < 2:
                    print(f"{round_name} has fewer than 2 rows — skipping.")
                    continue
                else:
                    print(f"Found valid standings in {round_name}")
                    return round_name

            except Exception as inner:
                print(f"⚠️ Could not process {round_name}: {inner}")

        print("No valid rounds with standings were found.")
        return None

    except Exception as e:
        print(f"Failed to locate round selector: {e}")
        return None

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
    
    table_data = []
    
    round_to_scrape = find_valid_standings_round(driver)
    
    if not round_to_scrape:
        print("Aborting: No valid round.")
        return
    
    # scroll down a bit to show standings
    scroll_page(driver, pixels=900)
    sleep(3)
    
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
