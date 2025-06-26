# -*- coding: utf-8 -*-

"""Utility to query card usage in an archetype from a decklists CSV."""

from __future__ import annotations

import pandas as pd
from tabulate import tabulate


def query_card_usage(
    decklists_csv: str | None = None,
    card: str | None = None,
    archetype: str | None = None,
) -> pd.DataFrame:
    """Return usage statistics for a card within an archetype.

    Parameters
    ----------
    decklists_csv:
        Path to the decklists CSV. If ``None`` the user will be prompted.
    card:
        The card name. If ``None`` the user will be prompted.
    archetype:
        The archetype name. If ``None`` or empty the query spans all archetypes.
    """

    if decklists_csv is None:
        decklists_csv = input("Enter path to decklists CSV: ").strip()
    if card is None:
        card = input("Enter card name: ").strip()
    if archetype is None:
        archetype = input("Enter archetype (leave blank for all): ").strip() or None

    df = pd.read_csv(decklists_csv)

    # Normalize column names used across scripts
    rename_map = {
        "player": "pilot",
        "card name": "card",
        "quantity": "Copies",
        "wins": "Wins",
        "losses": "Losses",
        "tot": "Copies",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Ensure required columns exist
    required = {"pilot", "archetype", "card", "Copies", "Wins", "Losses", "loc"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing columns in CSV: {', '.join(sorted(missing))}")

    # Scope the dataframe based on the archetype provided
    df_archetype = df if not archetype else df[df["archetype"] == archetype]

    # Total unique pilots for this archetype
    total_pilots = df_archetype["pilot"].nunique()

    # Pilots who played the card
    pilots_with_card = df_archetype[df_archetype["card"] == card]["pilot"].unique()

    # Pilots in the archetype without the card
    pilots_without_card_df = df_archetype[~df_archetype["pilot"].isin(pilots_with_card)]
    unique_wins_losses = (
        pilots_without_card_df.groupby("pilot")[["Wins", "Losses"]].first().sum()
    )
    wins_without_card = unique_wins_losses["Wins"]
    losses_without_card = unique_wins_losses["Losses"]

    # Filter for selected card and archetype in the main deck
    filtered_df = df_archetype[
        (df_archetype["card"] == card) & (df_archetype["loc"] == "main")
    ]

    stats = (
        filtered_df.groupby("Copies")
        .agg({"Wins": "sum", "Losses": "sum", "pilot": "nunique"})
        .rename(columns={"pilot": "# of Pilots"})
    )

    stats[["card", "archetype"]] = card, archetype or "All"
    stats = stats.reset_index()[
        ["card", "archetype", "Copies", "# of Pilots", "Wins", "Losses"]
    ]

    pilots_with = filtered_df["pilot"].nunique()
    pilots_without = total_pilots - pilots_with

    zero_copies_row = pd.DataFrame(
        {
            "card": [card],
            "archetype": [archetype or "All"],
            "Copies": [0],
            "# of Pilots": [pilots_without],
            "Wins": [wins_without_card],
            "Losses": [losses_without_card],
        }
    )

    stats = pd.concat([zero_copies_row, stats], ignore_index=True)
    stats["Win%"] = (
        stats["Wins"] / (stats["Wins"] + stats["Losses"])
    ).fillna(0) * 100
    stats["Win%"] = stats["Win%"].round(2)

    print(tabulate(stats, headers="keys", tablefmt="mixed_outline"))
    return stats


if __name__ == "__main__":
    query_card_usage()