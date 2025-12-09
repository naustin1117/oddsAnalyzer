import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import '../styles/App.css'
import { apiGet } from '../api'
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
      <h1>NHL Odds Analyzer</h1>

      {/* HIGH Confidence Record */}
      {resultsSummary && (
        <div className="record-section">
          <h2>HIGH Confidence Record</h2>
          <div className="record-grid">
            <div className="record-card">
              <h3>Total</h3>
              <p className="record-stat">{resultsSummary.total.wins}-{resultsSummary.total.losses}-{resultsSummary.total.pushes}</p>
              <p className="win-rate">{resultsSummary.total.win_rate}% Win Rate</p>
              <p className={`units ${resultsSummary.total.total_units >= 0 ? 'positive' : 'negative'}`}>
                {resultsSummary.total.total_units >= 0 ? '+' : ''}{resultsSummary.total.total_units} units
              </p>
              <p className={`roi ${resultsSummary.total.roi >= 0 ? 'positive' : 'negative'}`}>
                {resultsSummary.total.roi >= 0 ? '+' : ''}{resultsSummary.total.roi}% ROI
              </p>
              <p className="total-bets">{resultsSummary.total.total_bets} bets</p>
            </div>
            <div className="record-card">
              <h3>Over Bets</h3>
              <p className="record-stat">{resultsSummary.over_bets.wins}-{resultsSummary.over_bets.losses}-{resultsSummary.over_bets.pushes}</p>
              <p className="win-rate">{resultsSummary.over_bets.win_rate}% Win Rate</p>
              <p className={`units ${resultsSummary.over_bets.total_units >= 0 ? 'positive' : 'negative'}`}>
                {resultsSummary.over_bets.total_units >= 0 ? '+' : ''}{resultsSummary.over_bets.total_units} units
              </p>
              <p className={`roi ${resultsSummary.over_bets.roi >= 0 ? 'positive' : 'negative'}`}>
                {resultsSummary.over_bets.roi >= 0 ? '+' : ''}{resultsSummary.over_bets.roi}% ROI
              </p>
              <p className="total-bets">{resultsSummary.over_bets.total_bets} bets</p>
            </div>
            <div className="record-card">
              <h3>Under Bets</h3>
              <p className="record-stat">{resultsSummary.under_bets.wins}-{resultsSummary.under_bets.losses}-{resultsSummary.under_bets.pushes}</p>
              <p className="win-rate">{resultsSummary.under_bets.win_rate}% Win Rate</p>
              <p className={`units ${resultsSummary.under_bets.total_units >= 0 ? 'positive' : 'negative'}`}>
                {resultsSummary.under_bets.total_units >= 0 ? '+' : ''}{resultsSummary.under_bets.total_units} units
              </p>
              <p className={`roi ${resultsSummary.under_bets.roi >= 0 ? 'positive' : 'negative'}`}>
                {resultsSummary.under_bets.roi >= 0 ? '+' : ''}{resultsSummary.under_bets.roi}% ROI
              </p>
              <p className="total-bets">{resultsSummary.under_bets.total_bets} bets</p>
            </div>
          </div>
        </div>
      )}

      {/* Health Status */}
      {health && (
        <div className="health-section">
          <h2>API Status</h2>
          <p>Status: <span style={{ color: 'green' }}>{health.status}</span></p>
          <p>Total Predictions: {health.predictions_count}</p>
          <p>Last Updated: {new Date(health.timestamp).toLocaleString()}</p>
        </div>
      )}

      {/* Today's Predictions */}
      {predictions && (
        <div className="predictions-section">
          <h2>Today's Predictions ({predictions.count})</h2>
          {predictions.count === 0 ? (
            <p>No predictions for today</p>
          ) : (
            <div className="predictions-grid">
              {predictions.predictions.map((pred, idx) => (
                <div
                  key={idx}
                  className="prediction-card clickable"
                  onClick={() => handlePredictionClick(pred.player_id)}
                >
                  <h3>{pred.player_name}</h3>
                  <p><strong>{pred.home_team} vs {pred.away_team}</strong></p>
                  <p>Line: {pred.line}</p>
                  <p>Model Prediction: {pred.prediction ? pred.prediction.toFixed(2) : 'N/A'}</p>
                  <p>Over: {pred.over_odds > 0 ? '+' : ''}{pred.over_odds} | Under: {pred.under_odds > 0 ? '+' : ''}{pred.under_odds}</p>
                  <p>Recommendation: {pred.recommendation}</p>
                  <p className={`confidence-${pred.confidence.toLowerCase()}`}>
                    {pred.confidence} confidence
                  </p>
                  <p style={{ fontSize: '0.8em', color: '#666' }}>
                    {new Date(pred.game_time).toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default Home