# src/utils/preprocess.py
import pandas as pd
import re

def summarize_game_data(raw_context: str) -> str:
    """Convert the retrieved raw play descriptions into a readable summary."""
    lines = [l.strip() for l in raw_context.split("\n") if l.strip()]
    df = pd.DataFrame({"desc": lines})

    # crude pattern match
    team_names = set()
    home_3pt, away_3pt = 0, 0

    for row in df["desc"]:
        if "3PT" in row:
            if "HOMEDESCRIPTION" in row or "HOME" in row:
                home_3pt += 1
            elif "VISITORDESCRIPTION" in row or "AWAY" in row:
                away_3pt += 1
        # extract simple team names
        m = re.findall(r"[A-Z][a-z]+", row)
        if m:
            team_names.update(m)

    summary = (
        f"Detected teams: {', '.join(list(team_names)[:2])}. "
        f"Home 3-pointers: {home_3pt}, Away 3-pointers: {away_3pt}. "
        f"Total 3PT events: {home_3pt + away_3pt}."
    )

    return summary
