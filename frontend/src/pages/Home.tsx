import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { PulseLoader } from 'react-spinners'
import './App.css'
import { apiGet, apiPost } from '../api'
import RecordStats from '../components/Home/RecordStats'
import PredictionsTable from '../components/Home/PredictionsTable'
import { PredictionsResponse, ResultsSummaryResponse, PlayerGamesResponse } from '../types'

function Home() {
  const [predictions, setPredictions] = useState<PredictionsResponse | null>(null)
  const [resultsSummary, setResultsSummary] = useState<ResultsSummaryResponse | null>(null)
  const [playerRecentGames, setPlayerRecentGames] = useState<Record<number, PlayerGamesResponse>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    // Fetch predictions on mount
    const fetchData = async () => {
      try {
        setLoading(true)

        // Fetch today's predictions (auth required)
        const predictionsData = await apiGet<PredictionsResponse>('/predictions/today')
        setPredictions(predictionsData)

        // Fetch results summary for HIGH confidence
        const summaryData = await apiGet<ResultsSummaryResponse>('/results/summary?confidence=HIGH')
        setResultsSummary(summaryData)

        // Fetch recent games for all players in a single bulk request
        const uniquePlayerIds = [...new Set(predictionsData.predictions.map(pred => pred.player_id))]
        const bulkGamesResponse = await apiPost<{ count: number; players: PlayerGamesResponse[] }>(
          '/players/bulk/recent-games',
          { player_ids: uniquePlayerIds, limit: 5 }
        )

        // Convert array response to map keyed by player_id
        const playerGamesMap: Record<number, PlayerGamesResponse> = {}
        bulkGamesResponse.players.forEach(playerData => {
          playerGamesMap[playerData.player_id] = playerData
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
    </div>
  )
}

export default Home