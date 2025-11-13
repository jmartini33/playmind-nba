#!/usr/bin/env python3
"""
End-to-end pipeline runner for PlayMind NBA.
Parses raw NBA play-by-play CSV data, then summarizes it into structured stats.
"""

import sys
import subprocess
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m src.run_pipeline <GAME_ID>")
        sys.exit(1)

    game_id = sys.argv[1]

    base_dir = Path(__file__).resolve().parents[1]
    raw_dir = base_dir / "data" / "raw"
    structured_dir = base_dir / "data" / "structured"

    # 0️⃣ Fetch raw play-by-play CSV
    print("🔸 Step 0: Fetching raw play-by-play data...")
    subprocess.run(["python", "-m", "src.ingestion.nba_data_loader", game_id], check=True)

    csv_path = raw_dir / f"{game_id}_game_data.csv"
    if not csv_path.exists():
        print(f"❌ Raw file not found: {csv_path}")
        sys.exit(1)

    print(f"\n🏀 Running full pipeline for game {game_id}...\n")

    # 1️⃣ Parse the game data
    print("🔹 Step 1: Parsing play-by-play data...")
    parse_cmd = [
        "python",
        "-m",
        "src.utils.parse_game_data",
        game_id,
    ]
    subprocess.run(parse_cmd, check=True)

    parsed_path = structured_dir / f"{game_id}_parsed.json"
    if not parsed_path.exists():
        print("❌ Parsing failed — parsed JSON not found.")
        sys.exit(1)

    print(f"✅ Parsed data saved to {parsed_path}\n")

    # 2️⃣ Summarize parsed data (input + output paths)
    print("🔹 Step 2: Summarizing parsed data...")
    summary_path = structured_dir / f"{game_id}_summary.json"
    summarize_cmd = [
        "python",
        "-m",
        "src.utils.summarize_parsed_data",
        game_id,
    ]
    subprocess.run(summarize_cmd, check=True)

    if not summary_path.exists():
        print("❌ Summarization failed — summary JSON not found.")
        sys.exit(1)

    print(f"✅ Summary data saved to {summary_path}\n")

    print("🎯 Pipeline completed successfully!\n")
    print(f"Parsed:   {parsed_path}")
    print(f"Summary:  {summary_path}\n")

    # 3️⃣ Ask user if they want to launch the QA engine
    choice = input("Would you like to run the QA engine now? (y/n): ").strip().lower()

    if choice in ["y", "yes"]:
        print("\n🚀 Launching QA Engine...\n")
        qa_cmd = [
            "python",
            "-m",
            "src.rag.qa_engine",
        ]
        subprocess.run(qa_cmd)
    else:
        print("\n✅ Pipeline complete. Skipping QA engine.\n")


if __name__ == "__main__":
    main()
