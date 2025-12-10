import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import '../styles/App.css'
import { apiGet } from '../api'
import RecordStats from '../components/Home/RecordStats'
import PredictionsTable from '../components/Home/PredictionsTable'
import { HealthResponse, PredictionsResponse, ResultsSummaryResponse } from '../types'

function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [predictions, setPredictions] = useState<PredictionsResponse | null>(null)
  const [resultsSummary, setResultsSummary] = useState<ResultsSummaryResponse | null>(null)
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
        <h1>NHL Odds Analyzer</h1>
        <p>Loading...</p>
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
        {/* Left Column - HIGH Confidence Record */}
        <div className="left-column">
          {resultsSummary && <RecordStats resultsSummary={resultsSummary} />}
        </div>

        {/* Right Column - Today's Predictions */}
        <div className="right-column">
          {predictions && (
            <div className="predictions-section">
              <PredictionsTable
                predictions={predictions.predictions}
                onPlayerClick={handlePredictionClick}
              />
            </div>
          )}
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