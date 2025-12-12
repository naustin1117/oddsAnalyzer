import { useState } from 'react'
import { Prediction, PlayerGamesResponse } from '../../types'
import PredictionsTableRow from './PredictionsTableRow'
import './PredictionsTable.css'

interface PredictionsTableProps {
  predictions: Prediction[]
  playerRecentGames: Record<number, PlayerGamesResponse>
  onPlayerClick: (playerId: number) => void
}

function PredictionsTable({ predictions, playerRecentGames, onPlayerClick }: PredictionsTableProps) {
  const [confidenceFilter, setConfidenceFilter] = useState<string | null>(null)

  // Filter predictions based on selected filters
  const filteredPredictions = predictions.filter((pred) => {
    if (confidenceFilter && pred.confidence.toUpperCase() !== confidenceFilter) {
      return false
    }
    return true
  })

  return (
    <div className="predictions-table-container">
      <div className="table-wrapper">
        <h2 className="predictions-header">Predictions</h2>

        {/* Only show filters if there are predictions */}
        {predictions.length > 0 && (
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
        )}

        <table className="predictions-table">
          <tbody>
            {predictions.length === 0 ? (
              <tr>
                <td colSpan={100} className="no-predictions-message">
                  No predictions for today
                </td>
              </tr>
            ) : (
              filteredPredictions.map((pred, idx) => (
                <PredictionsTableRow
                  key={idx}
                  prediction={pred}
                  playerRecentGames={playerRecentGames[pred.player_id]}
                  onPlayerClick={onPlayerClick}
                />
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default PredictionsTable