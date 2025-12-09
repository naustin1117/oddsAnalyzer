import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { apiGet } from '../api'
import RecentGamesTable from '../components/RecentGamesTable'
import { PlayerGamesResponse } from '../types'
import '../styles/Player.css'

function Player() {
  const { playerId } = useParams<{ playerId: string }>()
  const [playerData, setPlayerData] = useState<PlayerGamesResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchPlayerData = async () => {
      try {
        setLoading(true)
        const data = await apiGet<PlayerGamesResponse>(`/players/${playerId}/recent-games?limit=5`)
        setPlayerData(data)
        setLoading(false)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred')
        setLoading(false)
      }
    }

    fetchPlayerData()
  }, [playerId])

  if (loading) {
    return (
      <div className="Player">
        <Link to="/" className="back-link">← Back to Predictions</Link>
        <p>Loading...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="Player">
        <Link to="/" className="back-link">← Back to Predictions</Link>
        <p style={{ color: 'red' }}>Error: {error}</p>
      </div>
    )
  }

  if (!playerData) {
    return (
      <div className="Player">
        <Link to="/" className="back-link">← Back to Predictions</Link>
        <p>No player data available</p>
      </div>
    )
  }

  return (
    <div className="Player">
      <Link to="/" className="back-link">← Back to Predictions</Link>

      <div className="player-container">
        <div className="player-header">
          <img
            src={playerData.headshot_url}
            alt={playerData.player_name}
            className="player-headshot"
            onError={(e) => {
              e.currentTarget.style.display = 'none'
            }}
          />
          <div className="player-info">
            <h1>{playerData.player_name}</h1>
            <p className="player-team">{playerData.team}</p>
          </div>
        </div>

        <RecentGamesTable games={playerData.games} />

        <div className="player-averages">
          <h2>Season Averages (Last {playerData.games_count} Games)</h2>
          <div className="averages-grid">
            <div className="average-stat">
              <span className="stat-label">Shots/Game</span>
              <span className="stat-value">{playerData.averages.shots_per_game}</span>
            </div>
            <div className="average-stat">
              <span className="stat-label">Goals/Game</span>
              <span className="stat-value">{playerData.averages.goals_per_game}</span>
            </div>
            <div className="average-stat">
              <span className="stat-label">Assists/Game</span>
              <span className="stat-value">{playerData.averages.assists_per_game}</span>
            </div>
            <div className="average-stat">
              <span className="stat-label">Points/Game</span>
              <span className="stat-value">{playerData.averages.points_per_game}</span>
            </div>
            <div className="average-stat">
              <span className="stat-label">TOI/Game</span>
              <span className="stat-value">{playerData.averages.toi_per_game} min</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Player