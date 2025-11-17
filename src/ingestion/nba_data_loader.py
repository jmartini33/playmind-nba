# src/ingestion/nba_data_loader.py

from pathlib import Path

import pandas as pd
import requests


DATA_PATH = Path("data/raw")
DATA_PATH.mkdir(parents=True, exist_ok=True)


def fetch_game(game_id: str):
    """Fetch play-by-play data for a game from the new NBA CDN JSON endpoint.

    The endpoint format is:
      https://cdn.nba.com/static/json/liveData/playbyplay/playbyplay_<GAMEID>.json

    We normalize the JSON "actions" list into a DataFrame with at least the
    columns used elsewhere in the pipeline (e.g. build_index):
      - PCTIMESTRING
      - HOMEDESCRIPTION
      - VISITORDESCRIPTION

    For each action, we map the `description` field into either
    HOMEDESCRIPTION or VISITORDESCRIPTION based on the teamTricode.
    """

    print(f"Fetching play-by-play data for game {game_id} from NBA CDN...")

    url = f"https://cdn.nba.com/static/json/liveData/playbyplay/playbyplay_{game_id}.json"

    try:
        resp = requests.get(url, timeout=15)
        print("Status code:", resp.status_code)
        print("URL:", resp.url)
        resp.raise_for_status()

        data = resp.json()

        game = data.get("game") or {}
        actions = game.get("actions") or []

        if not actions:
            print("⚠️ No actions found in CDN response.")
            return None

        home_team = game.get("homeTeam") or {}
        away_team = game.get("awayTeam") or {}
        home_code = home_team.get("teamTricode")
        away_code = away_team.get("teamTricode")

        rows = []
        for action in actions:
            clock = action.get("clock", "")
            description = action.get("description", "") or ""
            team_tricode = action.get("teamTricode")

            # Map description into home/visitor columns based on team code
            home_desc = ""
            visitor_desc = ""
            if description:
                if team_tricode == home_code:
                    home_desc = description
                elif team_tricode == away_code:
                    visitor_desc = description
                else:
                    # Neutral events (jump balls, timeouts, etc.)
                    home_desc = description

            row = {
                "PCTIMESTRING": clock,
                "HOMEDESCRIPTION": home_desc,
                "VISITORDESCRIPTION": visitor_desc,
                "PERIOD": action.get("period"),
                "SCORE_HOME": action.get("scoreHome"),
                "SCORE_AWAY": action.get("scoreAway"),
                "ACTION_TYPE": action.get("actionType"),
                "PLAYER_ID": action.get("personId"),
                "PLAYER_NAME": action.get("playerNameI"),  # or another name field
                "TEAM_TRICODE": team_tricode,
            }
            rows.append(row)

        df = pd.DataFrame(rows)
        if df.empty:
            print("⚠️ CDN response produced an empty DataFrame.")
            return None

        return df

    except Exception:
        import traceback
        print("❌ Exception while fetching data from NBA CDN:")
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
