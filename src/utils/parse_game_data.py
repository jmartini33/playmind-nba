import re
import json
from pathlib import Path

RAW_DIR = Path("data/raw")
STRUCTURED_DIR = Path("data/structured")

def parse_event_type(description: str) -> str:
    desc = description.upper()
    if "3PT" in desc and "MISS" not in desc:
        return "3PT_MADE"
    if "3PT" in desc and "MISS" in desc:
        return "3PT_MISSED"
    if ("SHOT" in desc or "JUMPER" in desc or "FADEAWAY" in desc) and "MISS" not in desc and "CLOCK" not in desc:
        return "SHOT_MADE"
    if ("SHOT" in desc or "JUMPER" in desc or "FADEAWAY" in desc) and "MISS" in desc and "CLOCK" not in desc:
        return "SHOT_MISSED"
    if "LAYUP" in desc and "MISS" not in desc:
        return "LAYUP_MADE"
    if "LAYUP" in desc and "MISS" in desc:
        return "LAYUP_MISSED"
    if "DUNK" in desc and "MISS" not in desc:
        return "DUNK_MADE"
    if "DUNK" in desc and "MISS" in desc:
        return "DUNK_MISSED"
    if "FREE THROW" in desc and "MISS" not in desc:
        return "FT_MADE"
    if "FREE THROW" in desc and "MISS" in desc:
        return "FT_MISSED"
    if "REBOUND" in desc:
        return "REBOUND"
    if "FOUL" in desc and "TURNOVER" in desc:
        return "FOUL+TURNOVER"
    if "FOUL" in desc:
        return "FOUL"
    if "STEAL" in desc:
        return "STEAL"
    if "TURNOVER" in desc:
        return "TURNOVER"
    if "BLOCK" in desc:
        return "BLOCK"
    if "SUB" in desc:
        return "SUBSTITUTION"
    if "TIMEOUT" in desc:
        return "TIMEOUT"
    
    return "OTHER"


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
    home_team_name = None
    away_team_name = None

    for _, row in df.iterrows():
        # Normalize descriptions and choose the first non-empty
        home_val = row.get("HOMEDESCRIPTION")
        away_val = row.get("VISITORDESCRIPTION")
        home_desc = "" if str(home_val).lower() == "nan" else str(home_val or "").strip()
        away_desc = "" if str(away_val).lower() == "nan" else str(away_val or "").strip()
        desc = home_desc or away_desc

        if not desc:
            continue

        # Primary event (from whichever side has text)
        primary_is_home = bool(home_desc)
        primary_HoA = home_team if primary_is_home else away_team

        # With the new ingestion, TEAM_TRICODE holds the team identifier (e.g. "SAC", "BOS")
        raw_team = str(row.get("TEAM_TRICODE") or "").strip()
        if raw_team.lower() == "nan":  # guard against pandas NaN stringification
            raw_team = ""

        # Track first-seen codes for home/away so we can fall back if some rows omit TEAM_TRICODE
        if primary_is_home and not home_team_name and raw_team:
            home_team_name = raw_team
        if not primary_is_home and not away_team_name and raw_team:
            away_team_name = raw_team

        # Fallback: if this row has no team code, use the first-seen home/away code, or UNK
        if not raw_team:
            raw_team = (home_team_name if primary_is_home else away_team_name) or "UNK"

        primary_event = {
            "period": int(row.get("PERIOD", 0)),
            "time": str(row.get("PCTIMESTRING") or "").strip(),
            "HoA": primary_HoA,
            "team": raw_team,
            "player": str(row.get("PLAYER_NAME") or row.get("PLAYER1_NAME") or "").strip(),
            "event_type": parse_event_type(desc),
            "points": extract_points(desc),
            "description": desc.strip(),
            "home_description": home_desc,
            "away_description": away_desc,
        }
        parsed.append(primary_event)

        evt = parse_event_type(desc)
        if "SHOT" in evt or "DUNK" in evt or "LAYUP" in evt or "FREE THROW" in evt or "JUMPER" in evt or "FADEAWAY" in evt or "3PT" in evt:
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
