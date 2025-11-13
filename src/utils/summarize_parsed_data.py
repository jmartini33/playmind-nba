import json
from pathlib import Path
from collections import defaultdict, deque
from re import T

STRUCTURED_DIR = Path("data/structured")

def get_parsed_path(game_id: str) -> Path:
    return STRUCTURED_DIR / f"{game_id}_parsed.json"

def get_summary_path(game_id: str) -> Path:
    return STRUCTURED_DIR / f"{game_id}_summary.json"

def summarize_parsed_game(parsed_path: str, save_path: str | None = None):
    """
    Summarizes a parsed game JSON into team-level stats and narrative context.
    Produces both structured numeric output and a short natural-language summary.
    """

    with open(parsed_path, "r") as f:
        plays = json.load(f)

    if not plays:
        raise ValueError("Parsed file is empty or invalid.")

    # Derive teams early for use throughout (first two non-UNK teams by appearance)
    early_seen = []
    for p in plays:
        t = p.get("team")
        if t and t != "UNK" and t not in early_seen:
            early_seen.append(t)
        if len(early_seen) == 2:
            break
    # Placeholder names if not enough info yet; replaced later if needed
    team_a, team_b = (early_seen + ["UNK", "UNK"])[:2]

    team_stats = defaultdict(lambda: {"points": 0, "fg_Made": 0, "fg_Attempts": 0, "threePt_Attempts": 0, "threePt_Made": 0, "ft_Made": 0, "ft_Attempts": 0, "turnovers": 0, "rebounds": 0, "fouls": 0, "steals": 0})
    scoring_timeline = []  # [(team, points, time)]

    def opposite(t: str) -> str:
        if t == team_a:
            return team_b
        if t == team_b:
            return team_a
        return t  # if UNK or unseen, leave unchanged

    # --------------------------------------------
    # Aggregate stats
    # --------------------------------------------
    for play in plays:
        team = play.get("team", "UNK")
        evt = play.get("event_type", "")
        pts = play.get("points", 0)
        away_desc = play.get("away_description", "")

        if "3PT" in evt:
            team_stats[team]["threePt_Attempts"] += 1
            team_stats[team]["fg_Attempts"] +=1
            if "MADE" in evt:
                team_stats[team]["points"] += 3
                team_stats[team]["threePt_Made"] += 1
                team_stats[team]["fg_Made"] += 1
        elif "FT" in evt:
            team_stats[team]["ft_Attempts"] += 1
            if "MADE" in evt:
                team_stats[team]["points"] += 1
                team_stats[team]["ft_Made"] += 1
        elif "MADE" in evt and "3PT" not in evt and "FT" not in evt:
            team_stats[team]["points"] += 2
            team_stats[team]["fg_Made"] += 1
            team_stats[team]["fg_Attempts"] +=1
        elif "MISS" in evt and "3PT" not in evt and "FT" not in evt:
            team_stats[team]["fg_Attempts"] += 1
        elif "TURNOVER" in evt:
            team_stats[team]["turnovers"] += 1
            if "STEAL" in away_desc:
                team_stats[opposite(team)]["steals"] += 1
        elif "REBOUND" in evt:
            team_stats[team]["rebounds"] += 1
        elif "FOUL" in evt:
            team_stats[team]["fouls"] += 1
        elif "STEAL" in evt:
            team_stats[opposite(team)]["steals"] += 1
            team_stats[team]["turnovers"] += 1

        

    # --------------------------------------------
    # Compute simple momentum / scoring runs
    # --------------------------------------------
    runs = []
    current_team, run_pts = None, 0
    for team, pts, _ in scoring_timeline:
        if team == current_team:
            run_pts += pts
        else:
            if run_pts >= 8:
                runs.append((current_team, run_pts))
            current_team = team
            run_pts = pts
    if run_pts >= 8:
        runs.append((current_team, run_pts))

    # --------------------------------------------
    # Derive final structured summary
    # --------------------------------------------
    # If early detection missed anything (e.g., empty or single team), fall back to aggregated keys
    if team_a == "UNK" or team_b == "UNK" or team_a == team_b:
        teams = list(team_stats.keys())
        if len(teams) < 2:
            teams += ["UNK"]
        team_a, team_b = teams[:2]

    a_stats, b_stats = team_stats[team_a], team_stats[team_b]

    summary = {
        "teams": [team_a, team_b],
        "final_score": {team_a: a_stats["points"], team_b: b_stats["points"]},
        "three_pointers": {
            team_a: f"{a_stats['threePt_Made']}/{a_stats['threePt_Attempts']}", 
            team_b: f"{b_stats['threePt_Made']}/{b_stats['threePt_Attempts']}", 
        },
        "field_goals": {
            team_a: f"{a_stats['fg_Made']}/{a_stats['fg_Attempts']}",
            team_b: f"{b_stats['fg_Made']}/{b_stats['fg_Attempts']}",
        },
        "free_throws": {
            team_a: f"{a_stats['ft_Made']}/{a_stats['ft_Attempts']}",
            team_b: f"{b_stats['ft_Made']}/{b_stats['ft_Attempts']}",
        },
        "turnovers": {team_a: (a_stats["turnovers"]), team_b: b_stats["turnovers"]},
        "rebounds": {team_a: a_stats["rebounds"], team_b: b_stats["rebounds"]},
        "fouls": {team_a: a_stats["fouls"], team_b: b_stats["fouls"]},
        "steals": {team_a: a_stats["steals"], team_b: b_stats["steals"]},
        "scoring_runs": runs,
    }

    # --------------------------------------------
    # Build narrative summary
    # --------------------------------------------
    winner = team_a if a_stats["points"] > b_stats["points"] else team_b
    loser = team_b if winner == team_a else team_a
    margin = abs(a_stats["points"] - b_stats["points"])
    run_texts = [f"{team} had a {pts}-point run" for team, pts in runs]

    narrative = (
        f"{winner} defeated {loser} by {margin} points. "
        f"{winner} made {summary['three_pointers'][winner]} threes compared to "
        f"{summary['three_pointers'][loser]} by {loser}. "
        f"{winner} committed {summary['turnovers'][winner]} turnovers. "
        + (" ".join(run_texts) if run_texts else "")
    )

    summary["narrative"] = narrative

    # --------------------------------------------
    # Save and return
    # --------------------------------------------
    if save_path:
        out_path = Path(save_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"✅ Saved summarized game data: {out_path}")

    return summary


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m src.utils.summarize_parsed_data <GAME_ID>")
        sys.exit(1)

    game_id = sys.argv[1]
    parsed_path = get_parsed_path(game_id)
    save_path = get_summary_path(game_id)

    if not parsed_path.exists():
        print(f"❌ Parsed JSON not found: {parsed_path}")
        sys.exit(1)

    summarize_parsed_game(str(parsed_path), str(save_path))
