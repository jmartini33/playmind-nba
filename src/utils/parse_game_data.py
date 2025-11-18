import re
import json
from pathlib import Path

RAW_DIR = Path("data/raw")
STRUCTURED_DIR = Path("data/structured")

def parse_event_type(description: str, action_type: str | None) -> str:
    desc = (description or "").upper()
    at = (action_type or "").lower()

    if at == "3pt":
        return "3PT_MISSED" if "MISS" in desc else "3PT_MADE"
    if at == "2pt":
        # Use description to distinguish make vs miss
        return "SHOT_MISSED" if "MISS" in desc else "SHOT_MADE"
    if at == "freethrow":
        return "FT_MISSED" if "MISS" in desc else "FT_MADE"
    if at == "rebound":
        return "REBOUND"
    if at == "foul":
        return "FOUL"
    if at == "turnover":
        return "TURNOVER"
    if at == "steal":
        return "STEAL"
    if at == "block":
        return "BLOCK"
    if at == "timeout":
        return "TIMEOUT"
    if at == "substitution":
        return "SUBSTITUTION"
    if at == "jumpball":
        return "JUMPBALL"
    if at == "period":
        # The description will typically say Period Start/End
        if "START" in desc:
            return "PERIOD_START"
        if "END" in desc:
            return "PERIOD_END"
        return "PERIOD"

    


def extract_points(description: str) -> int:
    match = re.search(r"\((\d+)\s*PTS?\)", description.upper())
    return int(match.group(1)) if match else 0


def extract_player(description: str) -> str:
    match = re.match(r"([A-Za-z' .-]+)", description)
    return match.group(1).strip() if match else "Unknown"


def parse_game_data(game_id: str, csv_path: str, home_team="HOME", away_team="AWAY") -> list[dict]:
    import pandas as pd
    df = pd.read_csv(csv_path)
    parsed = []
    shotAttempts = 0

    # Infer home/away team tricodes from score changes
    def infer_home_away_codes(df: "pd.DataFrame"):
        home_code = None
        away_code = None
        last_home = None
        last_away = None

        for _, r in df.iterrows():
            team = r.get("TEAM_TRICODE")
            sh = r.get("SCORE_HOME")
            sa = r.get("SCORE_AWAY")

            if team and pd.notna(team) and pd.notna(sh) and pd.notna(sa):
                if last_home is not None and sh != last_home:
                    if home_code is None:
                        home_code = str(team)
                if last_away is not None and sa != last_away:
                    if away_code is None:
                        away_code = str(team)
                if home_code and away_code:
                    break

            last_home, last_away = sh, sa

        return home_code, away_code

    home_team_code, away_team_code = infer_home_away_codes(df)

    for _, row in df.iterrows():
        # Normalize descriptions and choose the first non-empty
        home_val = row.get("HOMEDESCRIPTION")
        away_val = row.get("VISITORDESCRIPTION")
        home_desc = "" if str(home_val).lower() == "nan" else str(home_val or "").strip()
        away_desc = "" if str(away_val).lower() == "nan" else str(away_val or "").strip()
        desc = home_desc or away_desc

        if not desc:
            continue

        # TEAM_TRICODE holds the team identifier (e.g. "SAC", "BOS")
        raw_team = str(row.get("TEAM_TRICODE") or "").strip()
        if raw_team.lower() == "nan":  # guard against pandas NaN stringification
            raw_team = ""

        # Map to home/away based on inferred game-level mapping
        if raw_team and home_team_code and raw_team == home_team_code:
            primary_HoA = home_team
        elif raw_team and away_team_code and raw_team == away_team_code:
            primary_HoA = away_team
        else:
            primary_HoA = "NEUTRAL"

        if not raw_team:
            raw_team = "UNK"

        # Prefer structured player name, but fall back to parsing description
        player_name = str(row.get("PLAYER_NAME") or row.get("PLAYER1_NAME") or "").strip()
        if not player_name and desc:
            player_name = extract_player(desc)

        action_type = str(row.get("ACTION_TYPE") or "").strip()
        evt_type = parse_event_type(desc, action_type)
        pts = extract_points(desc)

        primary_event = {
            "period": int(row.get("PERIOD", 0)),
            "time": str(row.get("PCTIMESTRING") or "").strip(),
            "HoA": primary_HoA,
            "team": raw_team,
            "player": player_name,
            "event_type": evt_type,
            "points": pts,
            "description": desc.strip(),
            "home_description": home_desc,
            "away_description": away_desc,
        }
        parsed.append(primary_event)

        evt = evt_type or ""
        if any(k in evt for k in ("SHOT", "DUNK", "LAYUP", "3PT", "FT")):
            if primary_HoA == away_team:
                shotAttempts += 1

    print(f"Shot attempts: {shotAttempts}")
    return parsed


def get_raw_csv_path(game_id: str) -> Path:
    return RAW_DIR / f"{game_id}_game_data.csv"


def save_parsed_game(game_id: str, output_dir: str = str(STRUCTURED_DIR)) -> str:
    csv_path = get_raw_csv_path(game_id)
    if not csv_path.exists():
        raise FileNotFoundError(f"Raw CSV not found: {csv_path}")

    data = parse_game_data(game_id, str(csv_path))
    out_path = Path(output_dir) / f"{game_id}_parsed.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved parsed game data: {out_path}")
    return str(out_path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m src.utils.parse_game_data <GAME_ID>")
        sys.exit(1)

    game_id = sys.argv[1]
    csv_path = get_raw_csv_path(game_id)

    if not csv_path.exists():
        print(f"Raw file not found: {csv_path}")
        sys.exit(1)

    print(f"Parsing game {game_id} from {csv_path}...")
    save_parsed_game(game_id)
