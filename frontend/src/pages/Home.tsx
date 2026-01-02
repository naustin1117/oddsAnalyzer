import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { PulseLoader } from 'react-spinners'
import './App.css'
import { apiGet } from '../api'
import RecordStats from '../components/Home/RecordStats'
import PredictionsTable from '../components/Home/PredictionsTable'
import { HealthResponse, PredictionsResponse, ResultsSummaryResponse, PlayerGamesResponse } from '../types'

function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [predictions, setPredictions] = useState<PredictionsResponse | null>(null)
  const [resultsSummary, setResultsSummary] = useState<ResultsSummaryResponse | null>(null)
  const [playerRecentGames, setPlayerRecentGames] = useState<Record<number, PlayerGamesResponse>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    // Fetch health status and predictions on mount
    const fetchData = async () => {
      try {
        setLoading(true)

        // Fetch health (no auth required)
        const healthData = await apiGet<HealthResponse>('/health')
        setHealth(healthData)

        // Fetch today's predictions (auth required)
        const predictionsData = await apiGet<PredictionsResponse>('/predictions/today')
        setPredictions(predictionsData)

        // Fetch results summary for HIGH confidence
        const summaryData = await apiGet<ResultsSummaryResponse>('/results/summary?confidence=HIGH')
        setResultsSummary(summaryData)

        // Fetch recent games for each unique player in predictions
        const uniquePlayerIds = [...new Set(predictionsData.predictions.map(pred => pred.player_id))]
        const playerGamesPromises = uniquePlayerIds.map(playerId =>
          apiGet<PlayerGamesResponse>(`/players/${playerId}/recent-games?limit=5`)
            .then(data => ({ playerId, data }))
            .catch(err => {
              console.error(`Failed to fetch games for player ${playerId}:`, err)
              return null
            })
        )

        const playerGamesResults = await Promise.all(playerGamesPromises)
        const playerGamesMap: Record<number, PlayerGamesResponse> = {}
        playerGamesResults.forEach(result => {
          if (result) {
            playerGamesMap[result.playerId] = result.data
          }
        })
        setPlayerRecentGames(playerGamesMap)

        setLoading(false)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred')
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  const handlePredictionClick = (playerId: number) => {
    navigate(`/player/${playerId}`)
  }

  if (loading) {
    return (
      <div className="App">
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '50vh',
          gap: '2rem'
        }}>
          <PulseLoader
            color="#646cff"
            size={15}
            speedMultiplier={0.8}
          />
          <p style={{ color: '#888' }}>Loading predictions...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="App">
        <h1>NHL Odds Analyzer</h1>
        <p style={{ color: 'red' }}>Error: {error}</p>
        <p style={{ fontSize: '0.9em', color: '#888' }}>
          Make sure the API is running on http://localhost:8000
        </p>
      </div>
    )
  }

  return (
    <div className="App">

      <div className="main-layout">
        {/* Left Column - Today's Predictions */}
        <div className="left-column">
          {predictions && (
            <div className="predictions-section">
              <PredictionsTable
                predictions={predictions.predictions}
                playerRecentGames={playerRecentGames}
                onPlayerClick={handlePredictionClick}
              />
            </div>
          )}
        </div>

        {/* Right Column - HIGH Confidence Record */}
        <div className="right-column">
          {resultsSummary && <RecordStats resultsSummary={resultsSummary} />}
        </div>
      </div>

      {/* API Status - Bottom Right Corner */}
      {health && (
        <div className="api-status-pill">
          <span className={`status-dot ${health.status === 'healthy' ? 'healthy' : 'error'}`}></span>
          <span className="status-text">API</span>
        </div>
      )}
    </div>
  )
}

export default Home