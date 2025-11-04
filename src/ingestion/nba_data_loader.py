# src/ingestion/nba_data_loader.py

from nba_api.stats.endpoints import playbyplayv2 as nba_data
import pandas as pd
from pathlib import Path


DATA_PATH = Path("data/raw")
DATA_PATH.mkdir(parents=True, exist_ok=True)


def fetch_game(game_id: str = "0022500142") -> pd.DataFrame:
    """
    Fetch play-by-play data for a given NBA game ID.
    Saves it to data/raw/ and returns a DataFrame.
    """
    print(f"Fetching play-by-play data for game {game_id}...")
    pbp = nba_data.PlayByPlayV2(game_id=game_id).get_data_frames()[0]

    out_path = DATA_PATH / f"{game_id}_game_data.csv"
    pbp.to_csv(out_path, index=False)

    print(f"Saved play-by-play data to {out_path}")
    return pbp


if __name__ == "__main__":
    df = fetch_game()
    print("Sample data:")
    print(df.head())
