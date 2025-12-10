import { useState } from 'react'
import { Prediction } from '../../types'
import './PredictionsTable.css'

interface PredictionsTableProps {
  predictions: Prediction[]
  onPlayerClick: (playerId: number) => void
}

function PredictionsTable({ predictions, onPlayerClick }: PredictionsTableProps) {
  const [confidenceFilter, setConfidenceFilter] = useState<string | null>(null)

  // Filter predictions based on selected filters
  const filteredPredictions = predictions.filter((pred) => {
    if (confidenceFilter && pred.confidence.toUpperCase() !== confidenceFilter) {
      return false
    }
    return true
  })

  if (predictions.length === 0) {
    return <p>No predictions for today</p>
  }

  return (
    <div className="predictions-table-container">
      <div className="table-wrapper">
        <h2 className="predictions-header">Predictions</h2>

        {/* Filters */}
        <div className="predictions-filters">
          <div className="filter-group">
            <button
              className={`filter-btn confidence-btn ${confidenceFilter === 'HIGH' ? 'active confidence-high' : ''}`}
              onClick={() => setConfidenceFilter(confidenceFilter === 'HIGH' ? null : 'HIGH')}
            >
              HIGH
            </button>
            <button
              className={`filter-btn confidence-btn ${confidenceFilter === 'MEDIUM' ? 'active confidence-medium' : ''}`}
              onClick={() => setConfidenceFilter(confidenceFilter === 'MEDIUM' ? null : 'MEDIUM')}
            >
              MEDIUM
            </button>
            <button
              className={`filter-btn confidence-btn ${confidenceFilter === 'LOW' ? 'active confidence-low' : ''}`}
              onClick={() => setConfidenceFilter(confidenceFilter === 'LOW' ? null : 'LOW')}
            >
              LOW
            </button>
          </div>
        </div>

        <table className="predictions-table">
          <tbody>
            {filteredPredictions.map((pred, idx) => (
              <tr
                key={idx}
                className="prediction-row clickable"
                onClick={() => onPlayerClick(pred.player_id)}
              >
                <td className="player-name">{pred.player_name}</td>
                <td className="matchup">{pred.home_team} vs {pred.away_team}</td>
                <td className="game-time">{new Date(pred.game_time).toLocaleString()}</td>
                <td className="line">{pred.line}</td>
                <td className="prediction">{pred.prediction ? pred.prediction.toFixed(2) : 'N/A'}</td>
                <td className="odds">
                  {pred.over_odds > 0 ? '+' : ''}{pred.over_odds} / {pred.under_odds > 0 ? '+' : ''}{pred.under_odds}
                </td>
                <td className="recommendation">{pred.recommendation}</td>
                <td>
                  <span className={`confidence-badge confidence-${pred.confidence.toLowerCase()}`}>
                    {pred.confidence}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default PredictionsTable