# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 14:58:06 2025

@author: jjwey
"""

"""

initialize packages to make it easier to call them in subsequent scrips

"""

from utils.browser_manager import BrowserManager
from utils.create_directory import create_tournament_folder
from utils.selenium_helpers import accept_cookies, scroll_page, wait_for_element
from utils.data_utils import save_df, load_pairings, get_unique_archetypes, filter_by_archetype, create_sub_folder