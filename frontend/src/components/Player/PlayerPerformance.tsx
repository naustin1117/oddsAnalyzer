import { useState } from 'react'
import PlayerStatsChart from './PlayerStatsChart'
import RecentGamesTable from './RecentGamesTable'
import { PlayerGame } from '../types'
import './PlayerPerformance.css'

interface PlayerPerformanceProps {
  games: PlayerGame[]
  line?: number
  prediction?: number
}

function PlayerPerformance({ games, line, prediction }: PlayerPerformanceProps) {
  const [activeTab, setActiveTab] = useState<'chart' | 'table'>('chart')

  return (
    <div className="player-performance">
      <div className="performance-tabs">
        <button
          className={`performance-tab ${activeTab === 'chart' ? 'active' : ''}`}
          onClick={() => setActiveTab('chart')}
        >
          Performance Chart
        </button>
        <button
          className={`performance-tab ${activeTab === 'table' ? 'active' : ''}`}
          onClick={() => setActiveTab('table')}
        >
          Recent Games
        </button>
      </div>

      {activeTab === 'chart' ? (
        <PlayerStatsChart games={games} line={line} prediction={prediction} />
      ) : (
        <RecentGamesTable games={games} />
      )}
    </div>
  )
}

export default PlayerPerformance