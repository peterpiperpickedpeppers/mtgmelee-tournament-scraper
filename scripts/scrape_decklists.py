# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 19:18:47 2025

@author: jjwey
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
    deck_ids = standings['deck id'].astype(str).tolist()#[:3]
    standings = pd.read_csv(standingsPath)
    
    # for each Deck ID, navigate to URL and scrape data
    for row in deck_ids:
        deckURL = os.path.join(CONFIG.decklistURL, row)
        driver.get(deckURL)
                
        # Wait for the player name element to ensure the page has loaded
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "decklist-card-title-author"))
        )
        
        # extract player name
        player_element = driver.find_element(By.CLASS_NAME, "decklist-card-title-author").find_element(By.TAG_NAME, "a")
        player_name = player_element.text
    
        # extract archetype
        archetype_element = driver.find_element(By.CLASS_NAME, "decklist-card-title")
        archetype = archetype_element.text
    
        # Locate the button containing the decklist
        button = driver.find_element(By.CLASS_NAME, "decklist-builder-copy-button")
    
        # Extract the decklist from the "data-clipboard-text" attribute
        decklist_text = button.get_attribute("data-clipboard-text")
    
        # split the decklist into maindeck and sideboard
        sections = decklist_text.split("Sideboard")
    
        main_deck_lines = sections[0].strip().split("\n")[1:]
        sideboard_lines = sections[1].strip().split("\n") if len(sections) > 1 else []
    
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
    
    # save all decklists
    save_df(all_decklists_df, filePath)
    
    print("Decklists scraped.")
