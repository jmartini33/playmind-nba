# 🏀 PlayMind: NBA Edition

An AI-powered NBA analytics platform using retrieval-augmented generation (RAG) to analyze play-by-play data and generate real-time tactical insights.

## 🚀 Setup Instructions

0. Install Python 3.11 (macOS example)

```bash
brew install python@3.11
```

1. Clone the repository

```bash
git clone https://github.com/jmartini33/playmind-nba.git
cd playmind-nba
```

2. Create and activate a virtual environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate  # macOS / Linux
# .venv\Scripts\activate  # Windows (PowerShell or cmd)
```

3. Install Python dependencies

```bash
pip install -r requirements.txt
```

4. Configure environment variables

If your QA engine or LLM backend needs API keys (for example `OPENAI_API_KEY`), create a `.env` file in the project root and add them there, for example:

```env
OPENAI_API_KEY=your_key_here
```

Your backend/config should load these from `.env` on startup (for example via `python-dotenv` or equivalent). Alternatively, you can still export them directly in your shell if you prefer.

## 🖥️ Running the backend (FastAPI API)

From the project root (with the virtualenv activated):

```bash
uvicorn src.api.server:app --reload
```

This will start the API server on `http://127.0.0.1:8000` by default.

- Games ingestion: `POST /api/games/ingest`
- List games: `GET /api/games`
- Game summary: `GET /api/games/{game_id}/summary`
- Ask about a game: `POST /api/games/{game_id}/ask`

## 🌐 Running the frontend (React + Vite)

In a separate terminal, from the project root:

```bash
cd playmind-nba-ui
npm install
npm run dev
```

By default Vite runs on `http://localhost:5173`.

The frontend expects the backend to be running locally (e.g. at `http://127.0.0.1:8000`) with the above API routes available.
