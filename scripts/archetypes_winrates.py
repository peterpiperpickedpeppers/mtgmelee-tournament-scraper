# -*- coding: utf-8 -*-
"""
@author: peterpiperpickedpeppers
Description: Calculates overall win rates using matchup results.
"""

import os
import pandas as pd
import numpy as np
import glob
from globals import CONFIG
from utils.data_utils import save_df

# future behavior for pandas
pd.set_option('future.no_silent_downcasting', True)

def create_archetype_winrates():
    """Determine global archetype winrates from matchups data."""
    print("Determining archetype winrates. . .")
    
    # find all matchup csvs in the matchups folder
    file_paths = glob.glob(os.path.join(CONFIG.matchups_folder, "*.csv"))
    
    # extract archetype names and compute win/loss totals
    data = [
        {
            'archetype': os.path.basename(file_path).split(' matchups')[0],
            'wins': (df := pd.read_csv(file_path))['wins'].sum(),
            'losses': df['losses'].sum(),
        }
        for file_path in file_paths
    ]
    
    # create dataframe
    df = pd.DataFrame(data)
    df["total matches"] = df["wins"] + df["losses"]
    df["winrate"] = (df["wins"] / df["total matches"].replace(0, np.nan)) * 100
    df["winrate"] = df["winrate"].fillna(0).infer_objects(copy=False)
    
    # save dataframe
    data_path = os.path.join(CONFIG.data_folder, f"{CONFIG.eventName} archetype winrates.csv")
    save_df(df, data_path)
        
    print("Archetype winrates file created.")
