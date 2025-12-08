import { useParams, Link } from 'react-router-dom'
import '../styles/Player.css'

function Player() {
  const { playerId } = useParams()

  return (
    <div className="Player">
      <Link to="/" className="back-link">← Back to Predictions</Link>

      <div className="player-container">
        <h1>Player Page</h1>
        <div className="player-id-display">
          <p className="player-id-label">Player ID:</p>
          <p className="player-id-value">{playerId}</p>
        </div>
      </div>
    </div>
  )
}

export default Player