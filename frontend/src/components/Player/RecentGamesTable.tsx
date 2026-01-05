import { PlayerGame } from '../types'
import './RecentGamesTable.css'

interface RecentGamesTableProps {
  games: PlayerGame[]
}

function RecentGamesTable({ games }: RecentGamesTableProps) {
  if (!games || games.length === 0) {
    return <p>No recent games available</p>
  }

  // Convert TOI from seconds to minutes for display
  const formatTOI = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${minutes}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="recent-games-table">
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Opponent</th>
            <th>Home/Away</th>
            <th>Shots</th>
            <th>Goals</th>
            <th>Assists</th>
            <th>Points</th>
            <th>TOI</th>
          </tr>
        </thead>
        <tbody>
          {games.map((game, idx) => (
            <tr key={idx}>
              <td>{game.game_date}</td>
              <td>{game.opponent}</td>
              <td>{game.home_away}</td>
              <td>{game.shots}</td>
              <td>{game.goals}</td>
              <td>{game.assists}</td>
              <td>{game.points}</td>
              <td>{formatTOI(game.toi_seconds)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default RecentGamesTable