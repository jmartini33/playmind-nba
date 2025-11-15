# src/ingestion/nba_data_loader.py

from nba_api.stats.endpoints import playbyplayv2 as nba_data
from nba_api.stats.library.http import NBAStatsHTTP
import pandas as pd
from pathlib import Path


DATA_PATH = Path("data/raw")
DATA_PATH.mkdir(parents=True, exist_ok=True)

def fetch_game(game_id: str):
    print(f"Fetching play-by-play data for game {game_id}...")

    try:
        # Use low-level HTTP client to avoid the broken get_data_sets() path
        http_client = NBAStatsHTTP()
        response = http_client.send_api_request(
            endpoint="playbyplayv2",
            parameters={"GameID": game_id},
        )

        # Log basic request info without relying on private attributes
        try:
            print("Status code:", response.get_status_code())
        except AttributeError:
            # Fallback if the client does not expose a status accessor
            print("Status code: <unavailable>")

        print("URL:", response.get_url())

        raw = response.get_dict()

        print("Top-level keys in response:", list(raw.keys()))

        if not isinstance(raw, dict):
            print("⚠️ API returned a non-dict response:")
            print(raw)
            return None

        if "resultSets" not in raw and "resultSet" not in raw:
            print("⚠️ API did not return legacy resultSets/resultSet structure.")
            print("Full response:")
            print(raw)
            return None

        # Normalize resultSets/resultSet to a list of result sets
        results = raw.get("resultSets") if "resultSets" in raw else raw.get("resultSet")
        if isinstance(results, dict):
            results = [results]

        if not results:
            print("⚠️ API returned no result sets.")
            return None

        first = results[0]
        headers = first.get("headers", [])
        row_set = first.get("rowSet", [])

        if not headers or not row_set:
            print("⚠️ result set missing headers or rowSet.")
            print(first)
            return None

        df = pd.DataFrame(row_set, columns=headers)
        if df.empty:
            print("⚠️ API returned an empty data frame after manual parse.")
            return None

        return df

    except Exception as e:
        import traceback
        print("❌ Exception while fetching data:")
        traceback.print_exc()
        raise


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
