# -*- coding: utf-8 -*-
"""
@author: peterpiperpickedpeppers
Description: Scrapes player decklists from MTGMelee.
"""
# set up workspace
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.data_utils import save_df
import pandas as pd
import os
from globals import CONFIG

def run_decklists_scraper():
    """Scrape decklists from the mtgmelee website."""
    print("Scraping decklists. . .")
    
    # variables
    standingsPath = os.path.join(CONFIG.data_folder, f"{CONFIG.eventName} standings.csv")
    filePath = os.path.join(CONFIG.data_folder, f"{CONFIG.eventName} all decklists.csv")
    all_decklists_df = pd.DataFrame(columns=['player', 'archetype', 'card name', 'quantity', 'loc'])
    
    # get broswer instance from globals
    driver = CONFIG.browser_instance
    sleep(3)
    
    # load deckIDs column from standings csv and convert to a list
    # then reload standings for later use
    standings = pd.read_csv(standingsPath, usecols=['deck id'])
    deck_ids = standings['deck id'].astype(str).tolist()
    standings = pd.read_csv(standingsPath)
    
    # for each Deck ID, navigate to URL and scrape data
    for row in deck_ids:
        deckURL = os.path.join(CONFIG.decklistURL, row)
        driver.get(deckURL)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "decklist-profile-image"))
        )
        
        player_name = driver.find_element(By.XPATH, "//a[contains(@href, '/Profile')]/span[@class='text-nowrap']").text

        def normalize_player_name(name):
            name = name.strip()
            if "," in name:
                # Likely a real name in "Last, First" format
                parts = name.split(",", 1)
                last = parts[0].strip()
                first = parts[1].strip()
                return f"{first} {last}"
            else:
                # Likely a handle or already-normalized
                return name

        player_name = normalize_player_name(player_name)

        # extract archetype
        archetype_element = driver.find_element(By.CLASS_NAME, "decklist-title")
        archetype = archetype_element.text
    
        # Find all category blocks
        categories = driver.find_elements(By.CLASS_NAME, "decklist-category")
        
        main_deck_lines = []
        sideboard_lines = []
        
        for category in categories:
            # Get the section title, e.g., "Planeswalker (2)", "Sideboard (15)"
            title_element = category.find_element(By.CLASS_NAME, "decklist-category-title")
            title_text = title_element.text.strip()
        
            # Determine whether we're in the main deck or sideboard
            is_sideboard = title_text.lower().startswith("sideboard")
        
            # Find all records in this category
            records = category.find_elements(By.CLASS_NAME, "decklist-record")
        
            for record in records:
                qty = record.find_element(By.CLASS_NAME, "decklist-record-quantity").text.strip()
                name = record.find_element(By.CLASS_NAME, "decklist-record-name").text.strip()
                line = f"{qty} {name}"
                if is_sideboard:
                    sideboard_lines.append(line)
                else:
                    main_deck_lines.append(line)
                    
        # function for parsing card entries into quantity and card name
        def parse_cards(lines):
            cards = []
            for line in lines:
                parts = line.split(" ", 1) # split into quantity and card name
                if len(parts) == 2:
                    qty, name = parts
                    cards.append({"quantity": int(qty), "card name": name})
            return cards
    
        # create DFs for maindeck and sideboard
        main_deck_df = pd.DataFrame(parse_cards(main_deck_lines))
        sideboard_df = pd.DataFrame(parse_cards(sideboard_lines))
    
        # merge and add player / archetype
        main_deck_df['loc'] = "main"
        sideboard_df['loc'] = "side"
        decklist_df = pd.concat([main_deck_df, sideboard_df], ignore_index=True)
        decklist_df['player'] = player_name
        decklist_df['archetype'] = archetype
        
        # Assign Wins from standings where 'Player' matches player_name
        decklist_df['wins'] = standings.loc[standings['player'] == player_name, 'wins'].values[0]
        decklist_df['losses'] = standings.loc[standings['player'] == player_name, 'losses'].values[0]
        decklist_df['draws'] = standings.loc[standings['player'] == player_name, 'draws'].values[0]
        
        # reset index
        decklist_df = decklist_df.reset_index()[['player', 'archetype', 'card name', 'quantity', 'loc', 'wins', 'losses', 'draws']]
        
        # concat with bigger df
        all_decklists_df = pd.concat([all_decklists_df, decklist_df], ignore_index=True)
        
        print(all_decklists_df)
        
    # save all decklists
    save_df(all_decklists_df, filePath)
    
    print("Decklists scraped.")
