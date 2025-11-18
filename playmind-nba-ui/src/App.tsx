import { useEffect, useState } from 'react'
import './App.css'
import BackgroundImage from './assets/BackgroundImage.png'

type Game = {
  id: string
  label: string
  home: string
  away: string
  score: string
}

function App() {
  const [games, setGames] = useState<Game[]>([])
  const [selectedGameId, setSelectedGameId] = useState<string | null>(null)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState<string | null>(null)
  const [answerStatus, setAnswerStatus] = useState<string | null>(null)
  const [ingestIds, setIngestIds] = useState('')
  const [ingestStatus, setIngestStatus] = useState<string | null>(null)
  const [gameSummary, setGameSummary] = useState<any | null>(null)
  const [gameSummaryStatus, setGameSummaryStatus] = useState<string | null>(null)
  const [reloadGamesKey, setReloadGamesKey] = useState(0)

  const hasGames = games.length > 0

  const selectedGame: Game | undefined =
    hasGames ? games.find((g) => g.id === selectedGameId) ?? games[0] : undefined

  useEffect(() => {
    async function loadGames() {
      try {
        const response = await fetch('/api/games')
        if (!response.ok) {
          // Keep UI usable even if backend is down
          return
        }
        const data: Game[] = await response.json()
        setGames(data)
        if (!selectedGameId && data.length > 0) {
          setSelectedGameId(data[0].id)
        }
      } catch {
        // Silent failure for now; could surface a toast later
      }
    }

    loadGames()
  }, [reloadGamesKey])

  useEffect(() => {
    if (!selectedGameId) {
      setGameSummary(null)
      setGameSummaryStatus(null)
      return
    }

    let cancelled = false

    async function loadSummary() {
      try {
        setGameSummaryStatus('Loading summary...')
        const response = await fetch(`/api/games/${selectedGameId}/summary`)
        if (!response.ok) {
          setGameSummary(null)
          setGameSummaryStatus('Summary is not available for this game yet.')
          return
        }
        const data = await response.json()
        if (!cancelled) {
          setGameSummary(data)
          setGameSummaryStatus(null)
        }
      } catch {
        if (!cancelled) {
          setGameSummary(null)
          setGameSummaryStatus('There was an error loading the summary for this game.')
        }
      }
    }

    loadSummary()

    return () => {
      cancelled = true
    }
  }, [selectedGameId])

  async function handleAskQuestion() {
    if (!selectedGame || !question.trim()) {
      return
    }

    try {
      setAnswer(null)
      setAnswerStatus('Asking AI...')

      const response = await fetch(`/api/games/${selectedGame.id}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question }),
      })

      if (!response.ok) {
        const text = await response.text()
        setAnswerStatus(`There was an error asking about this game: ${text}`)
        return
      }

      const data: { answer: string } = await response.json()
      setAnswer(data.answer)
      setAnswerStatus(null)
    } catch (error) {
      setAnswerStatus('There was an unexpected error asking about this game.')
    }
  }

  async function handleIngestGames() {
    const trimmed = ingestIds.trim()
    if (!trimmed) {
      setIngestStatus('Enter at least one game ID.')
      return
    }

    const ids = Array.from(
      new Set(
        trimmed
          .split(/[\s,]+/)
          .map((id) => id.trim())
          .filter(Boolean),
      ),
    )

    if (ids.length === 0) {
      setIngestStatus('Enter at least one game ID.')
      return
    }

    try {
      setIngestStatus('Ingesting games...')

      await Promise.all(
        ids.map(async (id) => {
          const response = await fetch('/api/games/ingest', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ gameId: id }),
          })

          if (!response.ok) {
            const text = await response.text()
            throw new Error(`Failed to ingest ${id}: ${text}`)
          }
        }),
      )

      setIngestStatus(`Ingested ${ids.length} game${ids.length > 1 ? 's' : ''}.`)
      // Trigger reload of games list so newly ingested games appear under "Select game"
      setReloadGamesKey((key) => key + 1)
    } catch (error) {
      setIngestStatus('There was an error ingesting one or more games. Check the server logs.')
    }
  }

  return (
    <div
      className="app"
      style={{
        backgroundImage: `url(${BackgroundImage})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
      }}
    >
      <header className="app-header">
        <div className="app-header-left">
          <div className="app-title">Playmind NBA</div>
        </div>
      </header>

      <main className="app-main app-main-games">
        <section className="app-section">
            <div className="card add-games-card">
              <div className="add-games-header">Add games by NBA Game ID</div>
              <div className="add-games-body">
                <input
                  className="add-games-input"
                  type="text"
                  placeholder="e.g. 0022500142, 0022500143"
                  value={ingestIds}
                  onChange={(event) => setIngestIds(event.target.value)}
                />
                <button
                  type="button"
                  className="add-games-button"
                  onClick={handleIngestGames}
                >
                  Ingest games
                </button>
              </div>
              <div className="add-games-hint">
                Paste one or more NBA game IDs from nba.com or stats.nba.com. We&apos;ll fetch, parse, and summarize them.
              </div>
              {ingestStatus && <div className="add-games-status">{ingestStatus}</div>}
            </div>

            <div className="games-layout">
              <div className="games-column games-column-left">
              <h2 className="section-title">Select game</h2>
              <div className="card games-list-card">
                {hasGames ? (
                  <div className="games-list">
                    {games.map((game) => (
                      <button
                        key={game.id}
                        type="button"
                        className={`games-list-item ${
                          game.id === selectedGameId ? 'active' : ''
                        }`}
                        onClick={() => setSelectedGameId(game.id)}
                      >
                        <div className="games-list-item-main">
                          {game.away} @ {game.home}
                        </div>
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="card-placeholder large">
                    No games have been ingested yet. Add a game above to get started.
                  </div>
                )}
              </div>
            </div>

            <div className="games-column games-column-middle">
              <h2 className="section-title">Summary</h2>
              <div className="card games-summary-card">
                {hasGames && selectedGame ? (
                  <>
                    <div className="games-summary-header">
                      <div className="games-summary-score">{selectedGame.score}</div>
                      <div className="games-summary-teams">
                        {selectedGame.away} @ {selectedGame.home}
                      </div>
                    </div>
                    <div className="games-summary-stats">
                      {gameSummaryStatus && (
                        <div className="games-summary-stat-line">{gameSummaryStatus}</div>
                      )}
                      {gameSummary && !gameSummaryStatus && (
                        <>
                          {gameSummary.teams && gameSummary.teams.length >= 2 && (
                            <div className="games-summary-grid">
                              {[gameSummary.teams[1], gameSummary.teams[0]].map((teamName) => (
                                <div className="games-summary-team" key={teamName}>
                                  <div className="games-summary-team-name">{teamName}</div>
                                  <div className="games-summary-team-stat">
                                    <strong>3PT:</strong>{' '}
                                    {gameSummary.three_pointers?.[teamName] ?? 'N/A'}
                                  </div>
                                  <div className="games-summary-team-stat">
                                    <strong>FG:</strong>{' '}
                                    {gameSummary.field_goals?.[teamName] ?? 'N/A'}
                                  </div>
                                  <div className="games-summary-team-stat">
                                    <strong>FT:</strong>{' '}
                                    {gameSummary.free_throws?.[teamName] ?? 'N/A'}
                                  </div>
                                  <div className="games-summary-team-stat">
                                    <strong>Turnovers:</strong>{' '}
                                    {gameSummary.turnovers?.[teamName] ?? 'N/A'}
                                  </div>
                                  <div className="games-summary-team-stat">
                                    <strong>Rebounds:</strong>{' '}
                                    {gameSummary.rebounds?.[teamName] ?? 'N/A'}
                                  </div>
                                  <div className="games-summary-team-stat">
                                    <strong>Fouls:</strong>{' '}
                                    {gameSummary.fouls?.[teamName] ?? 'N/A'}
                                  </div>
                                  <div className="games-summary-team-stat">
                                    <strong>Steals:</strong>{' '}
                                    {gameSummary.steals?.[teamName] ?? 'N/A'}
                                  </div>
                                  <div className="games-summary-team-stat">
                                    <strong>Blocks:</strong>{' '}
                                    {gameSummary.blocks?.[teamName] ?? 'N/A'}
                                  </div>
                                  <div className="games-summary-team-stat">
                                    <strong>Timeouts:</strong>{' '}
                                    {gameSummary.timeouts?.[teamName] ?? 'N/A'}
                                  </div>
                                  <div className="games-summary-team-stat">
                                    <strong>Substitutions:</strong>{' '}
                                    {gameSummary.substitutions?.[teamName] ?? 'N/A'}
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </>
                      )}
                      {!gameSummary && !gameSummaryStatus && (
                        <div className="games-summary-stat-line">
                          Summary data is not available for this game yet.
                        </div>
                      )}
                    </div>
                  </>
                ) : (
                  <div className="card-placeholder large">
                    {hasGames
                      ? 'Select a game to see details.'
                      : 'No summary available until at least one game has been ingested.'}
                  </div>
                )}
              </div>
            </div>

            <div className="games-column games-column-right">
              <h2 className="section-title">Ask about this game</h2>
              <div className="card games-qa-card">
                <div className="games-qa-row">
                  <textarea
                    className="games-question-input"
                    placeholder={
                      hasGames && selectedGame
                        ? 'Example: Why did the Celtics pull away in the 4th quarter?'
                        : 'Ingest a game above to start asking questions...'
                    }
                    value={question}
                    onChange={(event) => setQuestion(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' && !event.shiftKey) {
                        event.preventDefault()
                        if (question.trim() && selectedGame) {
                          void handleAskQuestion()
                        }
                      }
                    }}
                    disabled={!hasGames || !selectedGame}
                  />
                  <button
                    type="button"
                    className="app-nav-button games-ask-button"
                    disabled={!question.trim() || !selectedGame}
                    onClick={handleAskQuestion}
                  >
                    {answerStatus === 'Asking AI...' ? 'Asking...' : 'Ask AI'}
                  </button>
                </div>
                {answerStatus && answerStatus !== 'Asking AI...' && (
                  <div className="games-summary-stat-line">{answerStatus}</div>
                )}
                {answer && (
                  <div className="games-summary-stat-line">{answer}</div>
                )}
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}

export default App
