import { useEffect, useState } from 'react'
import './App.css'
import BackgroundImage2 from './assets/BackgroundImage2.jpg'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

type Game = {
  id: string
  label: string
  home: string
  away: string
  score: string
}

function App() {
  const [games, setGames] = useState<Game[]>([])
  const [selectedGameIds, setSelectedGameIds] = useState<string[]>([])
  const [activeSummaryGameId, setActiveSummaryGameId] = useState<string | null>(null)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState<string | null>(null)
  const [answerStatus, setAnswerStatus] = useState<string | null>(null)
  const [ingestIds, setIngestIds] = useState('')
  const [ingestStatus, setIngestStatus] = useState<string | null>(null)
  const [gameSummary, setGameSummary] = useState<any | null>(null)
  const [gameSummaryStatus, setGameSummaryStatus] = useState<string | null>(null)
  const [reloadGamesKey, setReloadGamesKey] = useState(0)
  const [summaryCache, setSummaryCache] = useState<Record<string, any>>({})
  const [summaryView, setSummaryView] = useState<'summary' | 'graph'>('summary')

  const hasGames = games.length > 0

  const selectedGame: Game | undefined =
    hasGames && activeSummaryGameId
      ? games.find((g) => g.id === activeSummaryGameId) ?? games[0]
      : hasGames
        ? games.find((g) => g.id === selectedGameIds[0]) ?? games[0]
        : undefined

  function toggleGameSelection(id: string) {
    setSelectedGameIds((prev) => {
      const exists = prev.includes(id)
      if (exists) {
        const next = prev.filter((g) => g !== id)
        if (activeSummaryGameId === id) {
          setActiveSummaryGameId(next[0] ?? null)
        }
        return next
      }
      setActiveSummaryGameId(id)
      return [...prev, id]
    })
  }

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
        if (data.length > 0 && selectedGameIds.length === 0) {
          setSelectedGameIds([data[0].id])
          setActiveSummaryGameId(data[0].id)
        }
      } catch {
        // Silent failure for now; could surface a toast later
      }
    }

    loadGames()
  }, [reloadGamesKey])

  useEffect(() => {
    if (!activeSummaryGameId) {
      setGameSummary(null)
      setGameSummaryStatus(null)
      return
    }

    let cancelled = false

    async function loadSummary() {
      try {
        // If we have this game's summary cached already, use it immediately.
        const key = activeSummaryGameId as string
        const cached = summaryCache[key]
        if (cached) {
          if (!cancelled) {
            setGameSummary(cached)
            setGameSummaryStatus(null)
          }
          return
        }

        setGameSummaryStatus('Loading summary...')
        const response = await fetch(`/api/games/${activeSummaryGameId}/summary`)
        if (!response.ok) {
          setGameSummary(null)
          setGameSummaryStatus('Summary is not available for this game yet.')
          return
        }
        const data = await response.json()
        if (!cancelled) {
          setGameSummary(data)
          setSummaryCache((prev) => ({ ...prev, [key]: data }))
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
  }, [activeSummaryGameId])

  async function handleAskQuestion() {
    if (!selectedGame || !question.trim() || selectedGameIds.length === 0) {
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
        body: JSON.stringify({ question, gameIds: selectedGameIds }),
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
        backgroundImage: `url(${BackgroundImage2})`,
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
              <h2 className="section-title">Game Select</h2>
              <div className="card games-list-card">
                {hasGames ? (
                  <div className="games-list">
                    {games.map((game) => {
                      const [awayScore, homeScore] = game.score.split(' - ')
                      return (
                        <button
                          key={game.id}
                          type="button"
                          className={`games-list-item ${
                            selectedGameIds.includes(game.id) ? 'active' : ''
                          }`}
                          onClick={() => toggleGameSelection(game.id)}
                        >
                          <div className="games-list-item-main">
                            {game.away} ({awayScore}) @ {game.home} ({homeScore})
                          </div>
                        </button>
                      )
                    })}
                  </div>
                ) : (
                  <div className="card-placeholder large">
                    No games have been ingested yet. Add a game above to get started.
                  </div>
                )}
              </div>
            </div>

            <div className="games-column games-column-middle">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 0 }}>
                <div className="games-summary-tabs" style={{ marginTop: 0 }}>
                  <button
                    type="button"
                    className={`games-summary-tab ${summaryView === 'summary' ? 'active' : ''}`}
                    onClick={() => setSummaryView('summary')}
                    style={{ padding: '6px 16px', fontSize: 13 }}
                  >
                    Summary
                  </button>
                  <button
                    type="button"
                    className={`games-summary-tab ${summaryView === 'graph' ? 'active' : ''}`}
                    onClick={() => setSummaryView('graph')}
                    style={{ padding: '6px 16px', fontSize: 13 }}
                  >
                    Graph
                  </button>
                </div>
              </div>
              <div className="card games-summary-card">
                {hasGames && selectedGame && selectedGameIds.length > 0 ? (
                  <>
                    <div className="games-summary-tabs">
                      {selectedGameIds.map((id) => {
                        const game = games.find((g) => g.id === id)
                        if (!game) return null
                        const isActive = id === activeSummaryGameId
                        return (
                          <button
                            key={id}
                            type="button"
                            className={`games-summary-tab ${isActive ? 'active' : ''}`}
                            onClick={() => setActiveSummaryGameId(id)}
                          >
                            {game.away} @ {game.home}
                          </button>
                        )
                      })}
                    </div>
                    <div className="games-summary-header">
                      {(() => {
                        const [awayScore, homeScore] = selectedGame.score.split(' - ')
                        const isGraph = summaryView === 'graph'
                        const awayColor = isGraph ? '#facc15' : undefined
                        const homeColor = isGraph ? '#3b82f6' : undefined
                        return (
                          <div className="games-summary-teams">
                            <span style={{ color: awayColor }}>
                              {selectedGame.away} ({awayScore})
                            </span>
                            {' @ '}
                            <span style={{ color: homeColor }}>
                              {selectedGame.home} ({homeScore})
                            </span>
                          </div>
                        )
                      })()}
                    </div>
                    <div className="games-summary-stats">
                      {gameSummaryStatus && (
                        <div className="games-summary-stat-line">{gameSummaryStatus}</div>
                      )}
                      {gameSummary && !gameSummaryStatus && summaryView === 'summary' && (
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
                      {gameSummary && !gameSummaryStatus && summaryView === 'graph' && (
                        <div style={{ height: 220 }}>
                          <ResponsiveContainer width="100%" height="100%">
                            <LineChart
                              data={(() => {
                                const teams = gameSummary.teams || []
                                if (teams.length < 2) return []
                                const [homeTeam, awayTeam] = teams

                                // Helper to parse "made/attempts" strings like "14/35" into percentage made
                                const getPct = (obj: any, team: string) => {
                                  const value = obj?.[team]
                                  if (!value || typeof value !== 'string') return 0
                                  const [made, attempts] = value.split('/')
                                  const m = Number(made)
                                  const a = Number(attempts)
                                  if (!Number.isFinite(m) || !Number.isFinite(a) || a === 0) return 0
                                  // Round to one decimal place
                                  return Math.round(((m / a) * 100) * 10) / 10
                                }
                                return [
                                  {
                                    stat: '3PT%',
                                    [homeTeam]: getPct(gameSummary.three_pointers, homeTeam),
                                    [awayTeam]: getPct(gameSummary.three_pointers, awayTeam),
                                  },
                                  {
                                    stat: 'FG%',
                                    [homeTeam]: getPct(gameSummary.field_goals, homeTeam),
                                    [awayTeam]: getPct(gameSummary.field_goals, awayTeam),
                                  },
                                  {
                                    stat: 'FT%',
                                    [homeTeam]: getPct(gameSummary.free_throws, homeTeam),
                                    [awayTeam]: getPct(gameSummary.free_throws, awayTeam),
                                  },
                                  {
                                    stat: 'REB',
                                    [homeTeam]: gameSummary.rebounds?.[homeTeam] ?? 0,
                                    [awayTeam]: gameSummary.rebounds?.[awayTeam] ?? 0,
                                  },
                                  {
                                    stat: 'TOV',
                                    [homeTeam]: gameSummary.turnovers?.[homeTeam] ?? 0,
                                    [awayTeam]: gameSummary.turnovers?.[awayTeam] ?? 0,
                                  },
                                  {
                                    stat: 'FOUL',
                                    [homeTeam]: gameSummary.fouls?.[homeTeam] ?? 0,
                                    [awayTeam]: gameSummary.fouls?.[awayTeam] ?? 0,
                                  },
                                  {
                                    stat: 'STL',
                                    [homeTeam]: gameSummary.steals?.[homeTeam] ?? 0,
                                    [awayTeam]: gameSummary.steals?.[awayTeam] ?? 0,
                                  },
                                  {
                                    stat: 'BLK',
                                    [homeTeam]: gameSummary.blocks?.[homeTeam] ?? 0,
                                    [awayTeam]: gameSummary.blocks?.[awayTeam] ?? 0,
                                  },
                                  {
                                    stat: 'TO',
                                    [homeTeam]: gameSummary.timeouts?.[homeTeam] ?? 0,
                                    [awayTeam]: gameSummary.timeouts?.[awayTeam] ?? 0,
                                  },
                                  {
                                    stat: 'SUB',
                                    [homeTeam]: gameSummary.substitutions?.[homeTeam] ?? 0,
                                    [awayTeam]: gameSummary.substitutions?.[awayTeam] ?? 0,
                                  },
                                  {
                                    stat: 'RUNS',
                                    [homeTeam]: gameSummary.scoring_runs?.[homeTeam] ?? 0,
                                    [awayTeam]: gameSummary.scoring_runs?.[awayTeam] ?? 0,
                                  },
                                ]
                              })()}
                            >
                              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                              <XAxis dataKey="stat" stroke="#9ca3af" />
                              <YAxis stroke="#9ca3af" allowDecimals={false} />
                              <Tooltip
                                contentStyle={{
                                  backgroundColor: '#020617',
                                  border: '1px solid #374151',
                                  fontSize: 12,
                                }}
                                formatter={(value: any, name: any, props: any) => {
                                  const stat = props?.payload?.stat as string | undefined
                                  const num = typeof value === 'number' ? value : Number(value)
                                  if (stat && ['3PT', 'FG', 'FT'].includes(stat) && Number.isFinite(num)) {
                                    return [`${num}%`, name]
                                  }
                                  return [value, name]
                                }}
                              />
                              <Legend />
                              <Line
                                type="monotone"
                                dataKey={gameSummary.teams?.[0]}
                                stroke="#3b82f6"
                                strokeWidth={2}
                                dot={{ r: 3 }}
                              />
                              <Line
                                type="monotone"
                                dataKey={gameSummary.teams?.[1]}
                                stroke="#facc15"
                                strokeWidth={2}
                                dot={{ r: 3 }}
                              />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>
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
                      ? 'Select one or more games to see details.'
                      : 'No summary available until at least one game has been ingested.'}
                  </div>
                )}
              </div>
            </div>

            <div className="games-column games-column-right">
              <h2 className="section-title">Ask AI</h2>
              <div className="card games-qa-card">
                <div className="games-qa-row">
                  <textarea
                    className="games-question-input"
                    placeholder={
                      hasGames && selectedGameIds.length > 0
                        ? 'Example: Compare these games or ask about a specific one.'
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
                    disabled={!question.trim() || !selectedGame || selectedGameIds.length === 0}
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
