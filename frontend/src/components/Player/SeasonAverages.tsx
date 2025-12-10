import { PlayerAverages } from '../types'
import './SeasonAverages.css'

interface SeasonAveragesProps {
  averages: PlayerAverages
  games_count: number
}

function SeasonAverages({ averages, games_count }: SeasonAveragesProps) {
  return (
    <div className="player-averages">
      <h2>Season Averages (Last {games_count} Games)</h2>
      <div className="averages-grid">
        <div className="average-stat">
          <span className="stat-label">Shots/Game</span>
          <span className="stat-value">{averages.shots_per_game}</span>
        </div>
        <div className="average-stat">
          <span className="stat-label">Goals/Game</span>
          <span className="stat-value">{averages.goals_per_game}</span>
        </div>
        <div className="average-stat">
          <span className="stat-label">Assists/Game</span>
          <span className="stat-value">{averages.assists_per_game}</span>
        </div>
        <div className="average-stat">
          <span className="stat-label">Points/Game</span>
          <span className="stat-value">{averages.points_per_game}</span>
        </div>
        <div className="average-stat">
          <span className="stat-label">TOI/Game</span>
          <span className="stat-value">{averages.toi_per_game} min</span>
        </div>
      </div>
    </div>
  )
}

export default SeasonAverages