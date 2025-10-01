# -*- coding: utf-8 -*-
"""Created on Wed Oct  1 13:38:59 2025 @author: peterpiperpickedpeppers."""
# -*- coding: utf-8 -*-

import os
import re
import pandas as pd
from time import sleep
from globals import CONFIG
from utils.data_utils import save_df

# Selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# -----------------------------
# CONFIG is assumed to be provided by your environment
# Must expose:
#   CONFIG.data_folder (str)
#   CONFIG.eventName (str)
#   CONFIG.decklistURL (base URL like "https://melee.gg/Decklist/View")
#   CONFIG.browser_instance (Selenium WebDriver)
# -----------------------------

# Modern rounds to count; Draft rounds are excluded
MODERN_ROUNDS = {4, 5, 6, 7, 8, 12, 13, 14, 15, 16}

def normalize_person_name(name: str) -> str:
    """Turn 'Last, First' into 'First Last', trim, collapse spaces, lowercase for matching."""
    if not name:
        return ""
    name = name.strip()
    if "," in name:
        last, first = [p.strip() for p in name.split(",", 1)]
        name = f"{first} {last}"
    return re.sub(r"\s+", " ", name).strip().lower()

def pretty_person_name(name: str) -> str:
    """Normalize, then restore Title Case for CSV display."""
    n = normalize_person_name(name)
    return " ".join(w.capitalize() for w in n.split())

def get_modern_record_from_page(driver, player_display_name: str) -> tuple[int, int]:
    """
    Scrape the 'Tournament Path' table on the current decklist page and return (wins, losses)
    limited to Modern rounds (4–8, 12–16). Byes are ignored.
    """
    me_norm = normalize_person_name(player_display_name)

    # Wait for the Tournament Path container if present; if not, return zeros
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "decklist-tournament-path-container"))
        )
    except Exception:
        return 0, 0

    rows = driver.find_elements(
        By.XPATH,
        "//div[@id='decklist-tournament-path-container']//table//tbody//tr"
    )

    wins = losses = 0

    for row in rows:
        tds = row.find_elements(By.TAG_NAME, "td")
        if len(tds) < 4:
            continue

        # Round number
        rnd_txt = tds[0].text.strip()
        try:
            rnd = int(rnd_txt)
        except ValueError:
            continue
        if rnd not in MODERN_ROUNDS:
            continue

        # Result text (e.g., "Player Name won 2-1-0" or "X was assigned a bye")
        result = tds[3].text.strip()

        # Skip Byes
        if "bye" in result.lower():
            continue

        # Extract winner name with a loose pattern "<name> won ..."
        m = re.match(r"^(?P<winner>.+?)\s+won\b", result, flags=re.IGNORECASE)
        if not m:
            # If a rare draw string appears, just ignore
            continue

        winner_norm = normalize_person_name(m.group("winner"))
        if winner_norm == me_norm:
            wins += 1
        else:
            losses += 1

    return wins, losses

def parse_cards(lines):
    """Parse 'qty name' strings into dicts with {'quantity': int, 'card name': str}."""
    cards = []
    for line in lines:
        parts = line.split(" ", 1)
        if len(parts) == 2:
            qty, name = parts
            try:
                qty = int(qty)
            except ValueError:
                continue
            cards.append({"quantity": qty, "card name": name})
    return cards

def robust_get_player_name(driver) -> str:
    """
    Extract player name from the decklist header. Handles both
    <a><span class='text-nowrap'>Last, First</span></a> and <a>Last, First</a>.
    Returns 'First Last' pretty-cased for display.
    """
    txt = ""
    # Try span version first
    elems = driver.find_elements(By.XPATH, "//a[contains(@href, '/Profile')]/span[@class='text-nowrap']")
    if elems:
        txt = elems[0].text.strip()
    else:
        # Fallback: first profile anchor text
        elems = driver.find_elements(By.XPATH, "//a[contains(@href, '/Profile')][1]")
        if elems:
            txt = elems[0].text.strip()
    return pretty_person_name(txt)

def save_df_fallback(df: pd.DataFrame, path: str):
    """Use your save_df if present; otherwise fallback to to_csv."""
    try:
        # If your codebase defines save_df, use it
        save_df(df, path)  # type: ignore[name-defined]
    except Exception:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df.to_csv(path, index=False)

def run_decklists_scraper():
    """Scrape decklists and compute Modern-only W/L from each decklist page."""
    print("Scraping decklists. . .")

    # Inputs/outputs
    standingsPath = os.path.join(CONFIG.data_folder, f"{CONFIG.eventName} standings.csv")
    filePath = os.path.join(CONFIG.data_folder, f"{CONFIG.eventName} all decklists.csv")

    # Output skeleton
    all_decklists_df = pd.DataFrame(
        columns=["player", "archetype", "card name", "quantity", "loc", "wins", "losses", "draws"]
    )

    # Selenium driver
    driver = CONFIG.browser_instance
    sleep(1)

    # Load deck IDs from standings (we only use 'deck id' to enumerate pages)
    standings = pd.read_csv(standingsPath, usecols=["deck id"])
    deck_ids = standings["deck id"].astype(str).tolist()

    for deck_id in deck_ids:
        deckURL = os.path.join(CONFIG.decklistURL, deck_id)
        driver.get(deckURL)

        # Wait for page to render a known element
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "decklist-title"))
        )

        # Player name (normalized for display)
        player_name = robust_get_player_name(driver)

        # Archetype (decklist title)
        archetype = driver.find_element(By.CLASS_NAME, "decklist-title").text.strip()

        # Collect categories
        categories = driver.find_elements(By.CLASS_NAME, "decklist-category")
        main_deck_lines, sideboard_lines = [], []

        for category in categories:
            # Title like "Creatures (16)" or "Sideboard (15)"
            title_text = category.find_element(By.CLASS_NAME, "decklist-category-title").text.strip()
            is_sideboard = title_text.lower().startswith("sideboard")

            # Records in this category
            records = category.find_elements(By.CLASS_NAME, "decklist-record")
            for record in records:
                qty = record.find_element(By.CLASS_NAME, "decklist-record-quantity").text.strip()
                name = record.find_element(By.CLASS_NAME, "decklist-record-name").text.strip()
                line = f"{qty} {name}"
                if is_sideboard:
                    sideboard_lines.append(line)
                else:
                    main_deck_lines.append(line)

        # Build decklist DataFrame
        main_deck_df = pd.DataFrame(parse_cards(main_deck_lines))
        sideboard_df = pd.DataFrame(parse_cards(sideboard_lines))
        if not main_deck_df.empty:
            main_deck_df["loc"] = "main"
        if not sideboard_df.empty:
            sideboard_df["loc"] = "side"

        decklist_df = pd.concat([main_deck_df, sideboard_df], ignore_index=True)
        if decklist_df.empty:
            # In case no categories/records were found, keep a single placeholder line
            decklist_df = pd.DataFrame([{"card name": "", "quantity": 0, "loc": "main"}])

        decklist_df["player"] = player_name
        decklist_df["archetype"] = archetype

        # --- NEW: Modern-only W/L from Tournament Path on this page ---
        try:
            modern_wins, modern_losses = get_modern_record_from_page(driver, player_name)
        except Exception:
            modern_wins, modern_losses = 0, 0

        decklist_df["wins"] = modern_wins
        decklist_df["losses"] = modern_losses
        decklist_df["draws"] = 0  # Modern rounds in these events typically don't show draws

        # Reorder columns and append
        decklist_df = decklist_df.reset_index(drop=True)[
            ["player", "archetype", "card name", "quantity", "loc", "wins", "losses", "draws"]
        ]
        all_decklists_df = pd.concat([all_decklists_df, decklist_df], ignore_index=True)

        print(f"{player_name} | {archetype} | Modern {modern_wins}-{modern_losses} | rows={len(decklist_df)}")

    # Save output
    save_df_fallback(all_decklists_df, filePath)
    print(f"Decklists scraped. Saved to: {filePath}")


# driver = CONFIG.browser_instance
# sleep(3)

# def test_one_deck(deck_id: str):
#     driver = CONFIG.browser_instance
#     deckURL = os.path.join(CONFIG.decklistURL, deck_id)
#     driver.get(deckURL)

#     # wait for page load
#     WebDriverWait(driver, 10).until(
#         EC.presence_of_element_located((By.CLASS_NAME, "decklist-title"))
#     )

#     player_name = robust_get_player_name(driver)
#     archetype = driver.find_element(By.CLASS_NAME, "decklist-title").text.strip()
#     modern_wins, modern_losses = get_modern_record_from_page(driver, player_name)

#     print(f"Testing {player_name} ({archetype}) → Modern {modern_wins}-{modern_losses}")


# deck_id = "3b7ab1fd-33d3-4c8c-be7f-b361002c912f"
# test_one_deck(deck_id)