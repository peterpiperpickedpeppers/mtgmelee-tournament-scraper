# -*- coding: utf-8 -*-
"""Created on Mon Sep 29 15:24:34 2025 @author: peterpiperpickedpeppers."""

import pandas as pd

decklist_path = r"C:\Users\jjwey\OneDrive\Desktop\Repositories\MTGMelee-Tournament-Scraper\data\PT Edge of Eternities 2025\PT Edge of Eternities 2025 all decklists.csv"

def archetype_card_copy_winrates(
    df: pd.DataFrame,
    archetype: str,
    loc: str | None = "main",   # set to None to include main+side
    min_pilots: int = 0,        # hide rows with tiny sample sizes
    max_copies_cap: int | None = None,  # e.g., 4 to force 0..4 even if max is lower
) -> pd.DataFrame:
    """
    Return a table: for each card in the archetype, the winrate by copy count
    (including 0 copies).
    Expected columns in df: player|pilot, archetype, card name|card, quantity|Copies, loc, wins|Wins, losses|Losses
    """

    # normalize columns
    df = df.rename(columns={
        "player": "pilot",
        "card name": "card",
        "quantity": "Copies",
        "wins": "Wins",
        "losses": "Losses",
    })

    df_arch = df[df["archetype"] == archetype].copy()
    if loc is not None:
        df_arch = df_arch[df_arch["loc"] == loc]

    # one result line per pilot
    pilot_results = df_arch.groupby("pilot")[["Wins", "Losses"]].first()

    # pilot × card -> Copies matrix (0 if card not present)
    deck_matrix = (
        df_arch.groupby(["pilot", "card"])["Copies"]
        .sum()
        .unstack(fill_value=0)
        .reindex(index=pilot_results.index)  # keep only pilots with results
        .fillna(0)
        .astype(int)
    )

    rows = []
    for card in deck_matrix.columns:
        max_obs = deck_matrix[card].max()
        copy_vals = range(0, (max_copies_cap or max_obs) + 1)

        for c in copy_vals:
            pilots = deck_matrix.index[deck_matrix[card] == c]
            n_pilots = len(pilots)
            if n_pilots < min_pilots:
                continue

            wr = pilot_results.loc[pilots].sum()
            wins = int(wr["Wins"]) if n_pilots > 0 else 0
            losses = int(wr["Losses"]) if n_pilots > 0 else 0
            total = wins + losses
            winp = round(100 * wins / total, 2) if total else 0.0

            rows.append({
                "card": card,
                "archetype": archetype,
                "Copies": c,
                "# of Pilots": n_pilots,
                "Wins": wins,
                "Losses": losses,
                "Win%": winp,
            })

    out = pd.DataFrame(rows).sort_values(["card", "Copies"]).reset_index(drop=True)
    return out


# --- usage ---
df = pd.read_csv(decklist_path)

archetype = "Izzet Affinity"
tbl = archetype_card_copy_winrates(
    df,
    archetype=archetype,
    loc="side",
    min_pilots=0,
    max_copies_cap=4
    )

# save
save_path2 = fr"C:\Users\jjwey\OneDrive\Desktop\Repositories\MTGMelee-Tournament-Scraper\data\PT Edge of Eternities 2025/{archetype} per card per copy winrates.csv"

tbl.to_csv(save_path2, index=False)
