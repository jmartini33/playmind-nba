from pathlib import Path
from typing import List
import subprocess

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.rag.qa_engine import build_llm, build_prompt
from src.service.data_service import ingest_game as ingest_game_service


# Lazily initialize LLM and prompt so the API can start even if OpenAI is misconfigured.
llm = None
prompt = None

BASE_DIR = Path(__file__).resolve().parents[2]
STRUCTURED_DIR = BASE_DIR / "data" / "structured"


class GameListItem(BaseModel):
  id: str
  label: str
  home: str
  away: str
  score: str


class IngestRequest(BaseModel):
  gameId: str


class AskRequest(BaseModel):
  question: str
  gameIds: List[str] | None = None


class AskResponse(BaseModel):
  answer: str


app = FastAPI(title="Playmind NBA API", version="0.1.0")


@app.post("/api/games/ingest")
async def ingest_game_endpoint(payload: IngestRequest):
  game_id = payload.gameId.strip()
  if not game_id:
    raise HTTPException(status_code=400, detail="gameId must not be empty")

  try:
    summary_path = ingest_game_service(game_id)
  except Exception as e:
    raise HTTPException(
      status_code=500,
      detail=f"Ingestion failed for game {game_id}: {e}",
    )

  return {"status": "ok", "gameId": game_id, "summaryPath": str(summary_path)}


@app.get("/api/games", response_model=List[GameListItem])
async def list_games() -> List[GameListItem]:
  if not STRUCTURED_DIR.exists():
    return []

  items: List[GameListItem] = []
  for path in sorted(STRUCTURED_DIR.glob("*_summary.json")):
    game_id = path.name.split("_summary.json")[0]

    try:
      import json

      with open(path, "r") as f:
        data = json.load(f)
    except Exception:
      continue

    teams = data.get("teams", ["HOME", "AWAY"])
    if len(teams) < 2:
      teams = (teams + ["UNK", "UNK"])[:2]

    fs = data.get("final_score", {})
    # Treat teams[0] as home, teams[1] as away
    home_team, away_team = teams[0], teams[1]
    home_score = fs.get(home_team, "-")
    away_score = fs.get(away_team, "-")
    score_str = f"{away_score} - {home_score}"

    # Label games in the conventional "away @ home" format
    label = f"{away_team} @ {home_team}"

    items.append(
      GameListItem(
        id=game_id,
        label=label,
        home=home_team,
        away=away_team,
        score=score_str,
      )
    )

  return items


@app.get("/api/games/{game_id}/summary")
async def get_game_summary(game_id: str):
  path = STRUCTURED_DIR / f"{game_id}_summary.json"
  if not path.exists():
    raise HTTPException(status_code=404, detail="Summary not found for that game_id")

  import json

  with open(path, "r") as f:
    data = json.load(f)

  return data


@app.post("/api/games/{game_id}/ask", response_model=AskResponse)
async def ask_about_game(game_id: str, payload: AskRequest):
  global llm, prompt

  # Lazily build the LLM and prompt on first use to avoid blocking startup
  if llm is None or prompt is None:
    llm = build_llm()
    prompt = build_prompt()

  if not payload.question.strip():
    raise HTTPException(status_code=400, detail="Question must not be empty")
  import json

  # Determine which game IDs to include in context
  game_ids = payload.gameIds or [game_id]

  contexts: List[str] = []
  for gid in game_ids:
    path = STRUCTURED_DIR / f"{gid}_summary.json"
    if not path.exists():
      continue

    with open(path, "r") as f:
      summary = json.load(f)

    teams = summary.get("teams", [])
    fs = summary.get("final_score", {})

    lines = []
    if len(teams) >= 2:
      lines.append(f"Game {gid}: {teams[0]} vs {teams[1]}.")
    if fs and len(teams) >= 2:
      lines.append(
        f"Final Score — {teams[0]}: {fs.get(teams[0], 'N/A')}, {teams[1]}: {fs.get(teams[1], 'N/A')}."
      )

    for stat in [
      "three_pointers",
      "field_goals",
      "free_throws",
      "turnovers",
      "rebounds",
      "fouls",
      "steals",
      "blocks",
      "timeouts",
      "substitutions",
      "scoring_runs",
    ]:
      s = summary.get(stat, {})
      if len(teams) >= 2 and s:
        lines.append(
          f"{stat.replace('_', ' ').title()} — {teams[0]}: {s.get(teams[0], 'N/A')}, {teams[1]}: {s.get(teams[1], 'N/A')}."
        )

    narrative = summary.get("narrative", "")
    if narrative:
      lines.append(f"Narrative: {narrative}")

    contexts.append("\n".join(lines))

  if not contexts:
    raise HTTPException(status_code=404, detail="No summaries found for the requested games")

  context = "\n\n".join(contexts)

  input_text = prompt.format(context=context, question=payload.question)
  result = llm.invoke(input_text)

  if isinstance(result, dict) and "generated_text" in result:
    answer_text: str = str(result["generated_text"]).strip()
  else:
    answer_text = str(result).strip()

  return AskResponse(answer=answer_text)
