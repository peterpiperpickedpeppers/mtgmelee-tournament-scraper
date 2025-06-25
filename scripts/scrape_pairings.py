# -*- coding: utf-8 -*-
"""
Pairings scraper for the mtgmelee website.

"""

# set up workspace
from time import sleep
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from utils.selenium_helpers import wait_for_element, click_element
from utils.data_utils import save_df
import pandas as pd
import os
from globals import CONFIG

def run_pairings_scraper():
    """Scrapes tournament pairings from the mtgmelee website."""
    print("Scraping pairings. . .")

    # get browser instance from globals and reload tournament website
    driver = CONFIG.browser_instance
    sleep(4)
        
    # Automatically detect the number of rounds by counting started buttons
    round_buttons = wait_for_element(
        driver,
        "//div[@id='pairings-round-selector-container']//button[@data-is-started='True']",
        multiple=True
    )
    
    # Get the total number of rounds
    total_rounds = len(round_buttons) - 3 # don't count the quarters, semis, or finals
    
    # create empty list
    data = []
     
    for i in range(1, total_rounds + 1):
        
        # Click the round button
        click_element(driver, f"//div[@id='pairings-round-selector-container']//button[@data-name='Round {i}']")
        
        sleep(2)
        
        # get number of pages in this round
        pagination_container = wait_for_element(driver, "//div[@id='tournament-pairings-table_paginate']")
        pagination_elements = driver.find_elements(By.XPATH, "//div[@id='tournament-pairings-table_paginate']//a[@tabindex]")
        page_numbers = [int(elem.text) for elem in pagination_elements if elem.text.isdigit()]
        total_pages = max(page_numbers) if page_numbers else 1
        
        # loop for each round (get info and go through the pages)
        for page in range(1, total_pages +1):
            sleep(1)
            
            # Click on the page number button directly
            try:
                click_element(driver, f"//div[@id='tournament-pairings-table_paginate']//a[text()='{page}']")
            
            except:
                
                break  # Exit pagination if there's an issue
                
            sleep(2)
            # Get page source, locate pairings table, find all rows
            sourceCode = driver.page_source
            soup = BeautifulSoup(sourceCode, 'lxml')
            table = soup.find('table', {'id': 'tournament-pairings-table'})
            rows = table.find('tbody').find_all('tr')
            
            # extract data
            data.extend(
                [
                    (
                        players[0].text.strip(),
                        players[1].text.strip(),
                        decks[0].text.strip() if len(decks) == 2 else '-',
                        decks[1].text.strip() if len(decks) == 2 else '-',
                        result.text.strip() if result else 'Unknown'
                    )
                    for row in rows
                    if (players := row.find_all('a', {'data-type': 'player'})) and len(players) == 2
                    and (decks := row.find_all('a', {'data-type': 'decklist'}))
                    and (result := row.find('td', class_='ResultString-column'))
                    ]
            )
    
    # convert extracted data to dataframe
    df = pd.DataFrame(data, columns=['Player1', 'Player2', 'Decklist1', 'Decklist2', 'Result'])
    
    # filter out draws and byes
    df = df[df['Result'].str.contains('Draw') == False]
    df = df[df['Result'].str.contains('Bye') == False]
    
    # split 'Result' column into two
    df[['WinningPlayer', 'Result']] = df.Result.str.rsplit(' won', expand=True, n = 1)
    
    # remove any results that don't have two decks
    df = df[df['Decklist1'].str.contains('-') == False]
    df = df[df['Decklist2'].str.contains('-') == False]
    
    # save data frame
    filePath = os.path.join(CONFIG.data_folder, f"{CONFIG.eventName} all pairings.csv")
    save_df(df, filePath)
    
    print("Pairings scraped.")
