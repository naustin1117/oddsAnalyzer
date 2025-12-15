import { useState } from 'react'
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from 'recharts'
import { PlayerGame } from '../types'
import './PlayerStatsChart.css'

interface PlayerStatsChartProps {
  games: PlayerGame[]
  line?: number
  prediction?: number
}

function PlayerStatsChart({ games, line, prediction }: PlayerStatsChartProps) {
  const [gamesFilter, setGamesFilter] = useState<5 | 10>(5)

  if (!games || games.length === 0) {
    return <p>No game data available</p>
  }

  // Filter games based on selected view
  const filteredGames = games.slice(0, gamesFilter)

  // Reverse games to show chronologically (oldest to newest)
  const chartData = [...filteredGames].reverse().map((game) => {
    let barColor = '#646cff' // Default color

    if (line !== undefined && prediction !== undefined) {
      // Model recommending UNDER (prediction < line)
      if (prediction < line) {
        // Green if shots were under the line, red if over
        barColor = game.shots < line ? '#4ade80' : '#ef4444'
      }
      // Model recommending OVER (prediction >= line)
      else {
        // Green if shots were over the line, red if under
        barColor = game.shots >= line ? '#4ade80' : '#ef4444'
      }
    }

    return {
      date: game.game_date,
      shots: game.shots,
      goals: game.goals,
      assists: game.assists,
      points: game.points,
      opponent: game.opponent,
      opponent_logo_url: game.opponent_logo_url,
      barColor,
    }
  })

  return (
    <div className="player-stats-chart">
      <div className="chart-header">
        <h2>Performance Trend</h2>
        <div className="chart-filters">
          <button
            className={`filter-btn ${gamesFilter === 5 ? 'active' : ''}`}
            onClick={() => setGamesFilter(5)}
          >
            Last 5 Games
          </button>
          <button
            className={`filter-btn ${gamesFilter === 10 ? 'active' : ''}`}
            onClick={() => setGamesFilter(10)}
          >
            Last 10 Games
          </button>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis
            dataKey="date"
            stroke="#888"
            tick={{ fill: '#888' }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis stroke="#888" tick={{ fill: '#888' }} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1a1a1a',
              border: '1px solid #333',
              borderRadius: '8px',
              color: '#fff',
            }}
            labelStyle={{ color: '#646cff' }}
            content={(props) => {
              if (!props.active || !props.payload || props.payload.length === 0) return null
              const data = props.payload[0].payload
              return (
                <div style={{
                  backgroundColor: '#1a1a1a',
                  border: '1px solid #333',
                  borderRadius: '8px',
                  padding: '10px',
                  color: '#fff',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    {data.opponent_logo_url && (
                      <img
                        src={data.opponent_logo_url}
                        alt={data.opponent}
                        style={{ width: '24px', height: '24px', objectFit: 'contain' }}
                      />
                    )}
                    <div>
                      <p style={{ margin: '0', color: '#646cff', fontWeight: 'bold', fontSize: '0.9em' }}>vs {data.opponent}</p>
                      <p style={{ margin: '0', color: '#888', fontSize: '0.8em' }}>{data.date}</p>
                    </div>
                  </div>
                  <p style={{ margin: '4px 0', color: '#646cff' }}>Shots: {data.shots}</p>
                  <p style={{ margin: '4px 0', color: '#4ade80' }}>Goals: {data.goals}</p>
                  <p style={{ margin: '4px 0', color: '#fbbf24' }}>Assists: {data.assists}</p>
                  <p style={{ margin: '4px 0', color: '#f87171' }}>Points: {data.points}</p>
                  {line !== undefined && prediction !== undefined && (
                    <>
                      <p style={{ margin: '8px 0 4px 0', color: '#888', fontSize: '0.9em' }}>
                        Line: {line} | Prediction: {prediction.toFixed(2)}
                      </p>
                      {prediction < line ? (
                        <p style={{ margin: '0', color: data.shots < line ? '#4ade80' : '#ef4444', fontWeight: 'bold' }}>
                          {data.shots < line ? '✓ UNDER would have won' : '✗ UNDER would have lost'}
                        </p>
                      ) : (
                        <p style={{ margin: '0', color: data.shots >= line ? '#4ade80' : '#ef4444', fontWeight: 'bold' }}>
                          {data.shots >= line ? '✓ OVER would have won' : '✗ OVER would have lost'}
                        </p>
                      )}
                    </>
                  )}
                </div>
              )
            }}
          />
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="line"
          />
          <Bar dataKey="shots" name="Shots">
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.barColor} />
            ))}
          </Bar>
          <Line
            type="monotone"
            dataKey="goals"
            stroke="#4ade80"
            strokeWidth={2}
            name="Goals"
            dot={{ fill: '#4ade80', r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="assists"
            stroke="#fbbf24"
            strokeWidth={2}
            name="Assists"
            dot={{ fill: '#fbbf24', r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="points"
            stroke="#f87171"
            strokeWidth={2}
            name="Points"
            dot={{ fill: '#f87171', r: 4 }}
          />
          {line !== undefined && (
            <ReferenceLine
              y={line}
              stroke="#ffffff"
              strokeWidth={2}
              label={{ value: `Line: ${line}`, position: 'right', fill: '#ffffff' }}
            />
          )}
          {prediction !== undefined && (
            <ReferenceLine
              y={prediction}
              stroke="#4ade80"
              strokeWidth={2}
              strokeDasharray="5 5"
              label={{ value: `Prediction: ${prediction.toFixed(2)}`, position: 'right', fill: '#4ade80' }}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

export default PlayerStatsChart