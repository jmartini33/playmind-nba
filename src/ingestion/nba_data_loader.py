# src/ingestion/nba_data_loader.py

from nba_api.stats.endpoints import playbyplayv2 as nba_data
import pandas as pd
from pathlib import Path


DATA_PATH = Path("data/raw")
DATA_PATH.mkdir(parents=True, exist_ok=True)

def fetch_game(game_id: str):
    print(f"Fetching play-by-play data for game {game_id}...")

    try:
        pbp = nba_data.PlayByPlayV2(game_id=game_id)
        raw = pbp.get_dict()

        # Debug: validate structure
        if not isinstance(raw, dict):
            print("⚠️ API returned a non-dict response:")
            print(raw)
            return None

        # Some responses come back without expected keys when blocked/rate-limited
        if "resultSets" not in raw:
            print("⚠️ API did not return valid play-by-play data (missing resultSets).")
            print("Full response:")
            print(raw)
            return None

        frames = pbp.get_data_frames()
        if not frames or frames[0].empty:
            print("⚠️ API returned an empty data frame.")
            return None

        return frames[0]

    except Exception as e:
        print(f"❌ Exception while fetching data: {e}")
        return None


def main():
    import sys
    from pathlib import Path

    if len(sys.argv) < 2:
        print("Usage: python -m src.ingestion.nba_data_loader <GAME_ID>")
        sys.exit(1)

    game_id = sys.argv[1]
    df = fetch_game(game_id)

    if df is None:
        print("❌ No data saved because the API did not return valid data.")
        sys.exit(1)

    out_dir = Path("data/raw")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{game_id}_game_data.csv"
    df.to_csv(out_path, index=False)
    print(f"✅ Saved play-by-play data to {out_path}")


if __name__ == "__main__":
    main()
