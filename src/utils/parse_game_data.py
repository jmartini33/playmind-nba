import re
import json
from pathlib import Path

def parse_event_type(description: str) -> str:
    desc = description.upper()
    if "3PT" in desc and "MISS" not in desc:
        return "3PT_MADE"
    if "3PT" in desc and "MISS" in desc:
        return "3PT_MISSED"
    if "SHOT" in desc and "MISS" not in desc:
        return "SHOT_MADE"
    if "SHOT" in desc and "MISS" in desc:
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
    if "FOUL" in desc:
        return "FOUL"
    if "STEAL" in desc:
        return "STEAL"
    if "TURNOVER" in desc:
        return "TURNOVER"
    if "FADEAWAY" in desc and "JUMPER" not in desc:
        return "FADEAWAY"
    if "JUMPER" in desc:
        return "JUMPER"
    
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

    for _, row in df.iterrows():
        home_desc = str(row.get("HOMEDESCRIPTION") or "").strip()
        away_desc = str(row.get("VISITORDESCRIPTION") or "").strip()
        desc = home_desc if home_desc != "nan" else away_desc

        if not desc:
            continue

        team = home_team if home_desc !="nan" else away_team
        parsed.append({
            "period": int(row.get("PERIOD", 0)),
            "time": str(row.get("PCTIMESTRING") or "").strip(),
            "HoA": team,
            "team": str(row.get("PLAYER1_TEAM_NICKNAME") or "").strip(),
            "player": str(row.get("PLAYER1_NAME") or "").strip(),
            "event_type": parse_event_type(desc),
            "points": extract_points(desc),
            "description": desc.strip()
        })

    return parsed


def save_parsed_game(game_id: str, csv_path: str, output_dir="data/structured") -> str:
    data = parse_game_data(game_id, csv_path)
    out_path = Path(output_dir) / f"{game_id}_parsed.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Saved parsed game data: {out_path}")
    return str(out_path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python -m src.utils.parse_game_data <game_id> <csv_path>")
        sys.exit(1)

    game_id = sys.argv[1]
    csv_path = sys.argv[2]

    print(f"Parsing game {game_id} from {csv_path}...")
    save_parsed_game(game_id, csv_path)
