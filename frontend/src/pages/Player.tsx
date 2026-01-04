import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { PulseLoader } from 'react-spinners'
import { apiGet } from '../api'
import PlayerHeader from '../components/Player/PlayerHeader'
import PlayerPerformance from '../components/Player/PlayerPerformance'
import SeasonAverages from '../components/Player/SeasonAverages'
import PlayerLineups from '../components/Player/PlayerLineups'
import AISummary from '../components/Player/AISummary'
import { PlayerGamesResponse, PlayerPredictionsResponse, LineupsResponse, PlayerNewsMap, PlayerNewsResponse } from '../types'
import './Player.css'

function Player() {
  const { playerId } = useParams<{ playerId: string }>()
  const [playerData, setPlayerData] = useState<PlayerGamesResponse | null>(null)
  const [predictionsData, setPredictionsData] = useState<PlayerPredictionsResponse | null>(null)
  const [lineupData, setLineupData] = useState<LineupsResponse | null>(null)
  const [newsData, setNewsData] = useState<PlayerNewsMap>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchPlayerData = async () => {
      try {
        setLoading(true)

        // Fetch player games and predictions first
        const [gamesData, predictions] = await Promise.all([
          apiGet<PlayerGamesResponse>(`/players/${playerId}/recent-games?full_season=true`),
          apiGet<PlayerPredictionsResponse>(`/players/${playerId}/predictions`)
        ])

        setPlayerData(gamesData)
        setPredictionsData(predictions)

        // Fetch lineup data using the team abbreviation
        try {
          const lineup = await apiGet<LineupsResponse>(`/lineups/${gamesData.team_abbrev}`)
          setLineupData(lineup)

          // Fetch news for IR players
          const fetchNewsForIRPlayers = async () => {
            const allPlayers = [
              ...lineup.team.line_combinations,
              ...lineup.team.goalies,
              ...lineup.team.injuries
            ]

            // Also check opponent if available
            if (lineup.opponent) {
              allPlayers.push(
                ...lineup.opponent.line_combinations,
                ...lineup.opponent.goalies,
                ...lineup.opponent.injuries
              )
            }

            // Filter for IR players with valid player_ids
            const irPlayers = allPlayers.filter(player =>
              player.injury_status?.toUpperCase().includes('IR') && player.player_id !== null
            )

            // Fetch news for each IR player
            const newsMap: PlayerNewsMap = {}

            await Promise.all(
              irPlayers.map(async (player) => {
                try {
                  const response = await apiGet<PlayerNewsResponse>(
                    `/players/${player.player_id}/news?limit=3`
                  )
                  if (response.news && response.news.length > 0) {
                    newsMap[player.player_name] = response.news
                  }
                } catch (err) {
                  // Silently fail for individual players - some might not have news
                  console.log(`No news found for ${player.player_name}`)
                }
              })
            )

            setNewsData(newsMap)
          }

          fetchNewsForIRPlayers()
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
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '50vh',
          gap: '2rem'
        }}>
          <PulseLoader
            color="#646cff"
            size={15}
            speedMultiplier={0.8}
          />
          <p style={{ color: '#888' }}>Loading player data...</p>
        </div>
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

  // Map suggested_time_filter to chart filter format
  const getInitialFilter = (suggestedFilter?: string | null): 5 | 10 | 'all' => {
    if (!suggestedFilter) return 5 // Default to Last 5

    switch (suggestedFilter) {
      case 'L5':
        return 5
      case 'L10':
        return 10
      case 'Season':
        return 'all'
      default:
        return 5
    }
  }

  return (
    <div className="Player">
      <div className="player-content-wrapper"
           style={{
        background: `linear-gradient(to bottom, transparent 0%, black 10%), linear-gradient(to right, ${playerData.primary_color}, ${playerData.secondary_color})`
      }}>
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
            {upcomingGame?.ai_summary && <AISummary summary={upcomingGame.ai_summary} />}
            <PlayerPerformance
              games={playerData.games}
              line={upcomingGame?.line}
              prediction={upcomingGame?.prediction ?? undefined}
              initialFilter={getInitialFilter(upcomingGame?.suggested_time_filter)}
            />
            <SeasonAverages averages={playerData.averages} games_count={playerData.games_count} />
          </div>

          {/* Lineup Information */}
          {lineupData && <PlayerLineups lineupData={lineupData} newsData={newsData} />}
        </div>
      </div>
    </div>
  )
}

export default Player