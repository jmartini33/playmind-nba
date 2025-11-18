from pathlib import Path

from src.ingestion.nba_data_loader import fetch_game
from src.utils.parse_game_data import get_raw_csv_path, save_parsed_game
from src.utils.summarize_parsed_data import (
    get_parsed_path,
    get_summary_path,
    summarize_parsed_game,
)


def ingest_game(game_id: str) -> Path:
    """End-to-end ingestion pipeline for a single NBA game.

    Steps:
      1. Fetch play-by-play JSON from the NBA CDN and write it to data/raw/<GAME_ID>_game_data.csv.
      2. Parse the raw CSV into structured play events and write data/structured/<GAME_ID>_parsed.json.
      3. Summarize the parsed game into team-level stats and write data/structured/<GAME_ID>_summary.json.

    Returns the path to the summary JSON file.
    """

    game_id = game_id.strip()
    if not game_id:
        raise ValueError("game_id must not be empty")

    try:
        # 0️⃣ Fetch raw play-by-play data from CDN and save to CSV
        df = fetch_game(game_id)
        if df is None:
            raise RuntimeError(f"No data returned from CDN for game {game_id}.")

        csv_path = get_raw_csv_path(game_id)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv_path, index=False)

        # 1️⃣ Parse raw CSV into structured play events
        parsed_path_str = save_parsed_game(game_id)
        parsed_path = Path(parsed_path_str)

        # 2️⃣ Summarize parsed game into team-level stats
        parsed_json_path = get_parsed_path(game_id)
        summary_path = get_summary_path(game_id)
        summarize_parsed_game(str(parsed_json_path), str(summary_path))

        return summary_path
        
    except Exception as e:
        import traceback
        print(f"Error in ingest_game for {game_id}: {e}")
        traceback.print_exc()
        raise
