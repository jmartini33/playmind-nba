import pandas as pd
import re


def summarize_game_data(raw_context: str) -> str:
    """Convert raw play-by-play lines into a quick summary."""
    if not isinstance(raw_context, str):
        raw_context = str(raw_context)

    lines = [str(l).strip() for l in raw_context.split("\n") if str(l).strip()]
    df = pd.DataFrame({"desc": lines})

    team_names = set()
    home_3pt, away_3pt = 0, 0

    for row in df["desc"]:
        text = str(row)
        if "3PT" in text:
            if "HOMEDESCRIPTION" in text or "HOME" in text:
                home_3pt += 1
            elif "VISITORDESCRIPTION" in text or "AWAY" in text:
                away_3pt += 1
        m = re.findall(r"[A-Z][a-z]+", text)
        if m:
            team_names.update(m)

    summary = (
        f"Detected teams: {', '.join(list(team_names)[:2]) or 'Unknown'}. "
        f"Home 3-pointers: {home_3pt}, Away 3-pointers: {away_3pt}. "
        f"Total 3PT events: {home_3pt + away_3pt}."
    )
    return summary


def preprocess_context(inputs: dict) -> dict:
    """Flatten and clean retrieved documents before summarization."""
    ctx = inputs.get("context", "")
    text_blocks = []

    if isinstance(ctx, list):
        for item in ctx:
            if hasattr(item, "page_content"):
                text_blocks.append(str(item.page_content))
            elif isinstance(item, dict) and "page_content" in item:
                text_blocks.append(str(item["page_content"]))
            else:
                text_blocks.append(str(item))
    else:
        text_blocks.append(str(ctx))

    flat_context = "\n".join(text_blocks)
    print(f"\n[Preprocessor] Retrieved {len(text_blocks)} chunks, {len(flat_context)} chars total.\n")

    summary = summarize_game_data(flat_context)
    return {"context": summary, "question": inputs["question"]}
