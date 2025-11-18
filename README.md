# 🏀 PlayMind: NBA Edition

An AI-powered NBA analytics platform using retrieval-augmented generation (RAG) to analyze play-by-play data and generate real-time tactical insights.

## 🚀 Setup Instructions (detailed)

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
# macOS / Linux
python3.11 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell or cmd)
python -m venv .venv
.venv\Scripts\activate
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

The backend is a FastAPI app defined in `src/api/server.py`. When running, it listens on `http://127.0.0.1:8000` by default and exposes the following routes:

- Games ingestion: `POST /api/games/ingest`
- List games: `GET /api/games`
- Game summary: `GET /api/games/{game_id}/summary`
- Ask about a game: `POST /api/games/{game_id}/ask`

See the **Quickstart** section below for the exact command to launch the backend.

## 🌐 Running the frontend (React + Vite)

The frontend is a React + Vite app in the `playmind-nba-ui` folder. When running in dev mode it listens on `http://localhost:5173` and proxies API calls to the backend.

See the **Quickstart** section below for the exact commands to install frontend dependencies and start the dev server.

## ⚡ Quickstart

From a fresh clone, these are the minimum steps to get everything running locally.

```bash
# 1) Clone and enter the repo
git clone https://github.com/jmartini33/playmind-nba.git
cd playmind-nba

# 2) Create + activate a virtualenv

# macOS / Linux
python3.11 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell example)
python -m venv .venv
.venv\Scripts\activate

# 3) Install backend dependencies
pip install -r requirements.txt

# 4) Start the backend API
uvicorn src.api.server:app --reload
```

In a **second terminal**:

```bash
cd playmind-nba/playmind-nba-ui
npm install
npm run dev
```

Then open `http://localhost:5173` in your browser. The UI is configured to talk to the backend at `http://127.0.0.1:8000`.

The frontend expects the backend to be running locally (e.g. at `http://127.0.0.1:8000`) with the above API routes available.
