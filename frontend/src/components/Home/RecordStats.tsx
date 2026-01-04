import { ResultsSummaryResponse } from '../types'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts'
import './RecordStats.css'

interface RecordStatsProps {
  resultsSummary: ResultsSummaryResponse
}

function RecordStats({ resultsSummary }: RecordStatsProps) {
  // Prepare data for the chart
  const chartData = [
    {
      category: 'Total',
      Wins: resultsSummary.total.wins,
      Losses: resultsSummary.total.losses,
      Pushes: resultsSummary.total.pushes,
    },
    {
      category: 'Over',
      Wins: resultsSummary.over_bets.wins,
      Losses: resultsSummary.over_bets.losses,
      Pushes: resultsSummary.over_bets.pushes,
    },
    {
      category: 'Under',
      Wins: resultsSummary.under_bets.wins,
      Losses: resultsSummary.under_bets.losses,
      Pushes: resultsSummary.under_bets.pushes,
    },
  ]

  return (
    <div className="record-stats">
      <h2>HIGH Confidence Record</h2>

      {/* Chart */}
      <div className="record-chart">
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="category" stroke="#888" tick={{ fill: '#888' }} />
            <YAxis stroke="#888" tick={{ fill: '#888' }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1a1a1a',
                border: '1px solid #333',
                borderRadius: '8px',
                color: '#fff',
                fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Oxygen", "Ubuntu", "Cantarell", sans-serif',
                fontSize: '0.75rem',
              }}
            />
            <Legend />
            <Bar dataKey="Wins" fill="#4ade80" />
            <Bar dataKey="Losses" fill="#ef4444" />
            <Bar dataKey="Pushes" fill="#888" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Stats tiles */}
      <div className="record-tiles">
        <div className="record-tile">
          <div className="tile-label">Total Record</div>
          <div className="tile-value">{resultsSummary.total.wins}-{resultsSummary.total.losses}-{resultsSummary.total.pushes}</div>
        </div>
        <div className="record-tile">
          <div className="tile-label">Win Rate</div>
          <div className="tile-value">{resultsSummary.total.win_rate}%</div>
        </div>
        <div className="record-tile">
          <div className="tile-label">Total Units</div>
          <div className={`tile-value ${resultsSummary.total.total_units >= 0 ? 'positive' : 'negative'}`}>
            {resultsSummary.total.total_units >= 0 ? '+' : ''}{resultsSummary.total.total_units}
          </div>
        </div>
        <div className="record-tile">
          <div className="tile-label">Total Bets</div>
          <div className="tile-value">{resultsSummary.total.total_bets}</div>
        </div>
      </div>
    </div>
  )
}

export default RecordStats