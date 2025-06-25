# -*- coding: utf-8 -*-
"""
@author: peterpiperpickedpeppers
Description: Creates win/loss statistics for archetype matchups.
"""
import pandas as pd
import numpy as np
import os
from utils.data_utils import save_df
from globals import CONFIG

def create_archetypes_matchups():
    """Processes pairings to create win/loss stats for each archetype."""
    print("Creating matchups files. . .")

    # Load list of unique archetypes correctly
    List_of_Archetypes = pd.read_csv(CONFIG.archetypes_file, header=None).squeeze().tolist()
    
    # Iterate over each archetype
    for archetype in List_of_Archetypes:
        
        # Open the archetype-specific results file
        results_file = os.path.join(CONFIG.results_folder, f"{archetype} results.csv")
        if not os.path.exists(results_file):
            print(f"Skipping {archetype}: No results file found.")
            continue

        df = pd.read_csv(results_file)

        # Ensure the necessary columns exist
        if not {'WinningPlayer', 'Player1', 'Decklist1', 'Decklist2'}.issubset(df.columns):
            print(f"Skipping {archetype}: Missing required columns in file.")
            continue

        # Create column with "winningdeck:losingdeck" pair
        df['DeckPair'] = np.where(
            df['WinningPlayer'] == df['Player1'],
            df['Decklist1'] + ':' + df['Decklist2'],
            df['Decklist2'] + ":" + df['Decklist1']
        )

        # Convert DeckPair column to list
        deck_pairs = df['DeckPair'].tolist()

        # Store win/loss results for matchups
        archetypeMatchups = []

        for matchup in List_of_Archetypes:
            if matchup == archetype:  # Avoid self-matchups
                continue

            # Construct matchup key for both win/loss scenarios
            archetype_wins = deck_pairs.count(f"{archetype}:{matchup}")
            archetype_losses = deck_pairs.count(f"{matchup}:{archetype}")
            total_matches = archetype_wins + archetype_losses

            if total_matches > 0:  # Only store matchups with actual games played
                archetypeMatchups.append([matchup, archetype_wins, archetype_losses, total_matches])

        # Convert list to DataFrame
        matchup_df = pd.DataFrame(archetypeMatchups, columns=[f"{archetype} vs.", 'wins', 'losses', 'totalmatches'])
        
        # Calculate winrate
        matchup_df['winrate'] = matchup_df['wins'] / matchup_df['totalmatches']

        # Save matchup data to CSV
        matchup_file = os.path.join(CONFIG.matchups_folder, f"{archetype} matchups.csv")
        save_df(matchup_df, matchup_file)

        print(f"Matchups file created for {archetype}.")

    print("All matchup files created.")

