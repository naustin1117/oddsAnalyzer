import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { apiGet } from '../api'
import PlayerHeader from '../components/Player/PlayerHeader'
import RecentGamesTable from '../components/Player/RecentGamesTable'
import PlayerStatsChart from '../components/Player/PlayerStatsChart'
import SeasonAverages from '../components/Player/SeasonAverages'
import PlayerLineups from '../components/Player/PlayerLineups'
import { PlayerGamesResponse, PlayerPredictionsResponse, LineupsResponse } from '../types'
import '../styles/Player.css'

function Player() {
  const { playerId } = useParams<{ playerId: string }>()
  const [playerData, setPlayerData] = useState<PlayerGamesResponse | null>(null)
  const [predictionsData, setPredictionsData] = useState<PlayerPredictionsResponse | null>(null)
  const [lineupData, setLineupData] = useState<LineupsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchPlayerData = async () => {
      try {
        setLoading(true)

        // Fetch player games and predictions first
        const [gamesData, predictions] = await Promise.all([
          apiGet<PlayerGamesResponse>(`/players/${playerId}/recent-games?limit=10`),
          apiGet<PlayerPredictionsResponse>(`/players/${playerId}/predictions`)
        ])

        setPlayerData(gamesData)
        setPredictionsData(predictions)

        // Fetch lineup data using the team abbreviation
        try {
          const lineup = await apiGet<LineupsResponse>(`/lineups/${gamesData.team_abbrev}`)
          setLineupData(lineup)
        } catch (lineupErr) {
          // Lineup data is optional - team might not be playing today
          console.log('Lineup data not available:', lineupErr)
        }

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

  // Get upcoming game info if available
  const upcomingGame = predictionsData?.upcoming?.[0]

  return (
    <div className="Player">
      <div className="player-content-wrapper">
        <PlayerHeader
          headshot_url={playerData.headshot_url}
          team_logo_url={playerData.team_logo_url}
          player_name={playerData.player_name}
          team={playerData.team_abbrev}
          primary_color={playerData.primary_color}
          secondary_color={playerData.secondary_color}
          opponent={upcomingGame?.away_team_abbrev === playerData.team_abbrev ? upcomingGame?.home_team : upcomingGame?.away_team}
          game_time={upcomingGame?.game_time}
          line={upcomingGame?.line}
          prediction={upcomingGame?.prediction ?? undefined}
          over_odds={upcomingGame?.over_odds}
          under_odds={upcomingGame?.under_odds}
        />

        {/* Main content: Graph + Season Averages on left, Lineups on right */}
        <div className="chart-and-lineups-wrapper">
          <div className="chart-column">
            <PlayerStatsChart
              games={playerData.games}
              line={upcomingGame?.line}
              prediction={upcomingGame?.prediction ?? undefined}
            />
            <SeasonAverages averages={playerData.averages} games_count={playerData.games_count} />
          </div>

          {/* Lineup Information */}
          {lineupData && <PlayerLineups lineupData={lineupData} />}
        </div>

        <RecentGamesTable games={playerData.games} />
      </div>
    </div>
  )
}

export default Player