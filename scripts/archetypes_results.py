# -*- coding: utf-8 -*-
"""
Created on Sun Mar 19 11:30:39 2023

@author: jjwey
"""

import pandas as pd
import os
from globals import CONFIG
from utils.data_utils import save_df, load_pairings, get_unique_archetypes, filter_by_archetype

def create_archetypes_results():
    """Filter pairings file to create results files for each archetype."""
    print("Filtering pairings. . .")

    # load in pairings file
    filePath = os.path.join(CONFIG.data_folder, f"{CONFIG.eventName} all pairings.csv")
    df = load_pairings(filePath)
    
    # get list of unique archetypes
    archetypes = get_unique_archetypes(df)
    
    # filter standings to create results files for each archetype
    for archetype in archetypes:
        filtered_df = filter_by_archetype(df, archetype)
        save_path = os.path.join(CONFIG.results_folder, f"{archetype} results.csv")
        save_df(filtered_df, save_path)
    
    # save list of archetypes
    archetypes_df = pd.DataFrame(archetypes, columns=['archetypes'])
    CONFIG.archetypes_file = os.path.join(CONFIG.data_folder, f"{CONFIG.eventName} archetypes.csv")
    save_df(archetypes_df, CONFIG.archetypes_file)
    
    print("Results files created.")
