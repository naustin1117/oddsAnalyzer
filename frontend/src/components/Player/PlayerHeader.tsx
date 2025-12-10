import { Link } from 'react-router-dom'
import './PlayerHeader.css'

interface PlayerHeaderProps {
  headshot_url: string
  team_logo_url: string
  player_name: string
  team: string
  // Optional upcoming game info
  opponent?: string
  game_time?: string
  line?: number
  prediction?: number
  over_odds?: number
  under_odds?: number
}

function PlayerHeader({
  headshot_url,
  team_logo_url,
  player_name,
  team,
  opponent,
  game_time,
  line,
  prediction,
  over_odds,
  under_odds
}: PlayerHeaderProps) {
  const formatGameTime = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })
  }

  return (
    <div className="player-header-top">
      <div className="player-header-content">
        <Link to="/" className="back-link-header">← Back to Predictions</Link>

        <div className="player-header-main">
          <div className="player-header-info">
            <div className="player-headshot-container">
              <img
                src={headshot_url}
                alt={player_name}
                className="player-headshot"
                onError={(e) => {
                  e.currentTarget.style.display = 'none'
                }}
              />
              <img
                src={team_logo_url}
                alt={`${team} logo`}
                className="team-logo-badge"
                onError={(e) => {
                  e.currentTarget.style.display = 'none'
                }}
              />
            </div>
            <div className="player-info">
              <h1>{player_name}</h1>
              <p className="player-team">{team}</p>
            </div>
          </div>

          {opponent && game_time && (
            <div className="game-info">
              <div className="game-info-row">
                <span className="game-label">Next Game:</span>
                <span className="game-value">vs {opponent}</span>
              </div>
              <div className="game-info-row">
                <span className="game-label">Time:</span>
                <span className="game-value">{formatGameTime(game_time)}</span>
              </div>
              {line !== undefined && (
                <div className="game-info-row">
                  <span className="game-label">Line:</span>
                  <span className="game-value">{line} shots</span>
                </div>
              )}
              {prediction !== undefined && (
                <div className="game-info-row">
                  <span className="game-label">Model:</span>
                  <span className="game-value prediction-value">{prediction.toFixed(2)} shots</span>
                </div>
              )}
              {(over_odds !== undefined || under_odds !== undefined) && (
                <div className="game-info-row">
                  <span className="game-label">Odds:</span>
                  <span className="game-value">
                    O: {over_odds !== undefined && (over_odds > 0 ? `+${over_odds}` : over_odds)} | U: {under_odds !== undefined && (under_odds > 0 ? `+${under_odds}` : under_odds)}
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default PlayerHeader