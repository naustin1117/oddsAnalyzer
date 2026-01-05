import { useState, useEffect } from 'react'
import { Prediction, PlayerGamesResponse } from '../../types'
import { ChevronRight, Brain } from 'lucide-react'
import './PredictionsTable.css'
import './PredictionsTableRow.css'

interface PredictionsTableRowProps {
  prediction: Prediction
  playerRecentGames?: PlayerGamesResponse
  onPlayerClick: (playerId: number) => void
}

function PredictionsTableRow({ prediction, playerRecentGames, onPlayerClick }: PredictionsTableRowProps) {
  const [revealedIndex, setRevealedIndex] = useState(0)
  const summaryLength = prediction.ai_summary?.length || 0
  const isTyping = revealedIndex < summaryLength

  useEffect(() => {
    if (!prediction.ai_summary) return

    let currentIndex = 0
    const typingSpeed = 20 // milliseconds per character

    const typeNextCharacter = () => {
      if (currentIndex < summaryLength) {
        setRevealedIndex(currentIndex + 1)
        currentIndex++
        setTimeout(typeNextCharacter, typingSpeed)
      }
    }

    // Wait 1.5 seconds before starting the animation
    setTimeout(() => {
      typeNextCharacter()
    }, 1500)
  }, [prediction.ai_summary, summaryLength])
  const checkGameHitLine = (shots: number, line: number, recommendation: string): boolean => {
    if (recommendation.includes('OVER')) {
      return shots > line
    } else {
      return shots < line
    }
  }

  const formatGameTime = (dateString: string) => {
    const gameDate = new Date(dateString)
    const today = new Date()

    // Check if game is today
    const isToday = gameDate.toDateString() === today.toDateString()

    // Format time as "10:00 PM"
    const timeString = gameDate.toLocaleString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })

    if (isToday) {
      return `Today, ${timeString}`
    }

    // For other days, show "Tomorrow" or the date
    const tomorrow = new Date(today)
    tomorrow.setDate(today.getDate() + 1)
    const isTomorrow = gameDate.toDateString() === tomorrow.toDateString()

    if (isTomorrow) {
      return `Tomorrow, ${timeString}`
    }

    // For other dates, show month/day
    return gameDate.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })
  }

  return (
    <tr
      className="prediction-row clickable"
      onClick={() => onPlayerClick(prediction.player_id)}
    >
      <td colSpan={8} style={{ padding: '1rem' }}>
        <div className="prediction-row-content">
          {/* Top Row: Player, Matchup, Time, Confidence */}
          <div className="prediction-row-top">
            <div className="prediction-player-section">
              <div className="prediction-player-image-container">
                {playerRecentGames?.headshot_url ? (
                  <img
                    src={playerRecentGames.headshot_url}
                    alt={prediction.player_name}
                    className="prediction-player-headshot"
                  />
                ) : (
                  <div className="prediction-player-placeholder" />
                )}
                {playerRecentGames?.team_logo_url && (
                  <img
                    src={playerRecentGames.team_logo_url}
                    alt={`${prediction.player_team} logo`}
                    className="prediction-team-logo-badge"
                  />
                )}
              </div>
              <span className="prediction-player-name">{prediction.player_name}</span>
              {playerRecentGames?.team && (
                <span className="prediction-team-pill">{playerRecentGames.team}</span>
              )}
            </div>

            <div className="prediction-row-right">
              <span className="prediction-matchup">{prediction.home_team} vs {prediction.away_team}</span>
              <span className="prediction-game-time">
                {formatGameTime(prediction.game_time)}
              </span>
              <span className={`confidence-badge confidence-${prediction.confidence.toLowerCase()}`}>
                {prediction.confidence}
              </span>
            </div>
          </div>

          {/* AI Description (if present) */}
          {prediction.ai_summary && (
            <div className="prediction-ai-description">
              <span className="prediction-ai-badge">
                AI Analysis
                <span className="prediction-ai-icon-container">
                  <span className={`prediction-ai-spinner ${isTyping ? 'visible' : 'hidden'}`}></span>
                  <Brain
                    size={12}
                    className={`prediction-ai-complete-icon ${!isTyping ? 'visible' : 'hidden'}`}
                  />
                </span>
              </span>
              <p className="prediction-ai-text">
                {prediction.ai_summary.split('').map((char, index) => (
                  <span
                    key={index}
                    className={index < revealedIndex ? 'revealed' : 'hidden-char'}
                  >
                    {char}
                  </span>
                ))}
              </p>
            </div>
          )}

          {/* Bottom Row: Recommendation, Prediction, Odds */}
          <div className="prediction-row-bottom">
            <div className="prediction-recommendation-container">
              <ChevronRight size={10} className="prediction-recommendation-icon" />
              <span className="prediction-recommendation-value">
                {prediction.recommendation}
              </span>
            </div>
            <div>
              <span className="prediction-stat-label">Prediction:</span>
              <span className="prediction-stat-value">{prediction.prediction ? prediction.prediction.toFixed(2) : 'N/A'}</span>
            </div>
            <div>
              <span className="prediction-stat-label">Odds:</span>
              <div className="prediction-odds-container">
                <span className={`prediction-odds-side ${prediction.recommendation.includes('OVER') ? 'highlighted' : ''}`}>
                  {prediction.over_odds > 0 ? '+' : ''}{prediction.over_odds}
                </span>
                <span className={`prediction-odds-side ${prediction.recommendation.includes('UNDER') ? 'highlighted' : ''}`}>
                  {prediction.under_odds > 0 ? '+' : ''}{prediction.under_odds}
                </span>
              </div>
            </div>
            {playerRecentGames?.games && (
              <div className="prediction-games-dots">
                {playerRecentGames.games.slice(0, 5).map((game, idx) => {
                  const hit = checkGameHitLine(game.shots, prediction.line, prediction.recommendation)
                  return (
                    <div
                      key={idx}
                      className={`game-dot ${hit ? 'hit' : 'miss'}`}
                      title={`${game.shots} shots vs ${prediction.line} line`}
                    />
                  )
                })}
              </div>
            )}
          </div>
        </div>
      </td>
    </tr>
  )
}

export default PredictionsTableRow
