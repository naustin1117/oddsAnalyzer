import { useState } from 'react'
import { LineupsResponse } from '../../types'
import './PlayerLineups.css'

interface PlayerLineupsProps {
  lineupData: LineupsResponse
}

function PlayerLineups({ lineupData }: PlayerLineupsProps) {
  const [activeMainTab, setActiveMainTab] = useState<'lineups' | 'injuries'>('lineups')
  const [activeLineupTab, setActiveLineupTab] = useState<'team' | 'opponent'>('team')
  const [selectedLine, setSelectedLine] = useState<string>('')

  // Helper function to filter players by line (combines forward lines with defense pairs)
  const filterPlayersByLine = (players: any[]) => {
    if (!selectedLine) return players

    // For regular lines, combine forwards with corresponding defense
    if (selectedLine === 'f1' || selectedLine === 'f2' || selectedLine === 'f3') {
      const lineNum = selectedLine.charAt(1) // Get the number (1, 2, or 3)
      const forwardLine = `f${lineNum}`
      const defenseLine = `d${lineNum}`
      return players.filter(player => player.line_id === forwardLine || player.line_id === defenseLine)
    }

    // f4 has no corresponding defense
    return players.filter(player => player.line_id === selectedLine)
  }

  // Helper function to organize players by position for formation display
  const organizeByPosition = (players: any[]) => {
    const organized: { [key: string]: any } = {
      lw: null,
      c: null,
      rw: null,
      ld: null,
      rd: null
    }

    players.forEach(player => {
      const posId = player.position_id?.toLowerCase()
      if (posId && organized.hasOwnProperty(posId)) {
        organized[posId] = player
      }
    })

    return organized
  }

  // Helper function to check if line is a special teams unit (PP or PK)
  const isSpecialTeams = (lineId: string) => {
    return lineId === 'pp1' || lineId === 'pp2' || lineId === 'pk1' || lineId === 'pk2'
  }

  return (
    <div className="lineups-column">
      <div className="lineups-section">
        {/* Main Tabs */}
        <div className="main-tabs">
          <button
            className={`main-tab ${activeMainTab === 'lineups' ? 'active' : ''}`}
            onClick={() => setActiveMainTab('lineups')}
          >
            Lineups
          </button>
          <button
            className={`main-tab ${activeMainTab === 'injuries' ? 'active' : ''}`}
            onClick={() => setActiveMainTab('injuries')}
          >
            Injuries/News
          </button>
        </div>

        {/* Content */}
        {activeMainTab === 'lineups' && (
          <div>
            {/* Tabs */}
            <div className="lineup-tabs">
          <button
            className={`lineup-tab ${activeLineupTab === 'team' ? 'active' : ''}`}
            onClick={() => setActiveLineupTab('team')}
          >
            {lineupData.team.team_name}
          </button>
          {lineupData.opponent && (
            <button
              className={`lineup-tab ${activeLineupTab === 'opponent' ? 'active' : ''}`}
              onClick={() => setActiveLineupTab('opponent')}
            >
              {lineupData.opponent.team_name}
            </button>
          )}
        </div>

        {/* Line Filter */}
        <div className="line-filter">
          <button
            className={`line-tile ${selectedLine === 'f1' ? 'active' : ''}`}
            onClick={() => setSelectedLine(selectedLine === 'f1' ? '' : 'f1')}
          >
            L1
          </button>
          <button
            className={`line-tile ${selectedLine === 'f2' ? 'active' : ''}`}
            onClick={() => setSelectedLine(selectedLine === 'f2' ? '' : 'f2')}
          >
            L2
          </button>
          <button
            className={`line-tile ${selectedLine === 'f3' ? 'active' : ''}`}
            onClick={() => setSelectedLine(selectedLine === 'f3' ? '' : 'f3')}
          >
            L3
          </button>
          <button
            className={`line-tile ${selectedLine === 'f4' ? 'active' : ''}`}
            onClick={() => setSelectedLine(selectedLine === 'f4' ? '' : 'f4')}
          >
            L4
          </button>
          <button
            className={`line-tile ${selectedLine === 'pp1' ? 'active' : ''}`}
            onClick={() => setSelectedLine(selectedLine === 'pp1' ? '' : 'pp1')}
          >
            PP1
          </button>
          <button
            className={`line-tile ${selectedLine === 'pp2' ? 'active' : ''}`}
            onClick={() => setSelectedLine(selectedLine === 'pp2' ? '' : 'pp2')}
          >
            PP2
          </button>
          <button
            className={`line-tile ${selectedLine === 'pk1' ? 'active' : ''}`}
            onClick={() => setSelectedLine(selectedLine === 'pk1' ? '' : 'pk1')}
          >
            PK1
          </button>
          <button
            className={`line-tile ${selectedLine === 'pk2' ? 'active' : ''}`}
            onClick={() => setSelectedLine(selectedLine === 'pk2' ? '' : 'pk2')}
          >
            PK2
          </button>
        </div>

        <div className="lineups-container">
          {/* Player's Team Lineup */}
          {activeLineupTab === 'team' && (
            <div className="team-lineup">
              <h3>{lineupData.team.team_name}</h3>
              {lineupData.team.opponent_name && (
                <p className="opponent-info">vs {lineupData.team.opponent_name}</p>
              )}

              {/* Hockey Formation Display */}
              {selectedLine ? (
                // Show single line formation
                (() => {
                  const filteredPlayers = filterPlayersByLine(lineupData.team.line_combinations)

                  // Check if this is a special teams unit (PP or PK)
                  if (isSpecialTeams(selectedLine)) {
                    // Display special teams as a grid of skaters
                    return (
                      <div className="formation-container">
                        <div className="formation-row special-teams">
                          {filteredPlayers.map((player, idx) => (
                            <div key={idx} className="formation-player">
                              <div
                                className="player-circle"
                                style={{
                                  background: `linear-gradient(135deg, ${lineupData.team.primary_color} 0%, ${lineupData.team.secondary_color} 100%)`
                                }}
                              >
                                {player.headshot_url ? (
                                  <img src={player.headshot_url} alt={player.player_name} className="player-headshot" />
                                ) : (
                                  player.jersey_number || '?'
                                )}
                              </div>
                              <div className="player-label">{player.player_name}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )
                  }

                  // Regular 5v5 lines - organize by traditional positions
                  const formation = organizeByPosition(filteredPlayers)

                  return (
                    <div className="formation-container">
                      {/* Forwards */}
                      <div className="formation-row forwards">
                        {['lw', 'c', 'rw'].map(pos => {
                          const player = formation[pos]
                          return (
                            <div key={pos} className="formation-player">
                              {player ? (
                                <>
                                  <div
                                    className="player-circle"
                                    style={{
                                      background: `linear-gradient(135deg, ${lineupData.team.primary_color} 0%, ${lineupData.team.secondary_color} 100%)`
                                    }}
                                  >
                                    {player.headshot_url ? (
                                      <img src={player.headshot_url} alt={player.player_name} className="player-headshot" />
                                    ) : (
                                      player.jersey_number || '?'
                                    )}
                                  </div>
                                  <div className="player-label">{player.player_name}</div>
                                </>
                              ) : (
                                <>
                                  <div className="player-circle empty">—</div>
                                  <div className="player-label">Empty</div>
                                </>
                              )}
                            </div>
                          )
                        })}
                      </div>

                      {/* Defense */}
                      <div className="formation-row defense">
                        {['ld', 'rd'].map(pos => {
                          const player = formation[pos]
                          return (
                            <div key={pos} className="formation-player">
                              {player ? (
                                <>
                                  <div
                                    className="player-circle"
                                    style={{
                                      background: `linear-gradient(135deg, ${lineupData.team.primary_color} 0%, ${lineupData.team.secondary_color} 100%)`
                                    }}
                                  >
                                    {player.headshot_url ? (
                                      <img src={player.headshot_url} alt={player.player_name} className="player-headshot" />
                                    ) : (
                                      player.jersey_number || '?'
                                    )}
                                  </div>
                                  <div className="player-label">{player.player_name}</div>
                                </>
                              ) : (
                                <>
                                  <div className="player-circle empty">—</div>
                                  <div className="player-label">Empty</div>
                                </>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )
                })()
              ) : (
                // Show all lines stacked
                <div className="all-lines-container">
                  {/* Forward Lines Section */}
                  <div className="line-group">
                    {['f1', 'f2', 'f3', 'f4'].map(lineId => {
                      const linePlayers = lineupData.team.line_combinations.filter(p => p.line_id === lineId)
                      if (linePlayers.length === 0) return null

                      const formation = organizeByPosition(linePlayers)
                      const lineLabel = lineId.toUpperCase().replace('F', 'Line ')

                      return (
                        <div key={lineId} className="line-row">
                          <h5 className="line-label">{lineLabel}</h5>
                          <div className="formation-row forwards">
                            {['lw', 'c', 'rw'].map(pos => {
                              const player = formation[pos]
                              return (
                                <div key={pos} className="formation-player">
                                  {player ? (
                                    <>
                                      <div
                                        className="player-circle"
                                        style={{
                                          background: `linear-gradient(135deg, ${lineupData.team.primary_color} 0%, ${lineupData.team.secondary_color} 100%)`
                                        }}
                                      >
                                        {player.headshot_url ? (
                                          <img src={player.headshot_url} alt={player.player_name} className="player-headshot" />
                                        ) : (
                                          player.jersey_number || '?'
                                        )}
                                      </div>
                                      <div className="player-label">{player.player_name}</div>
                                    </>
                                  ) : (
                                    <>
                                      <div className="player-circle empty">—</div>
                                      <div className="player-label">Empty</div>
                                    </>
                                  )}
                                </div>
                              )
                            })}
                          </div>
                        </div>
                      )
                    })}
                  </div>

                  {/* Defense Pairs Section */}
                  <div className="line-group">
                    {['d1', 'd2', 'd3'].map(lineId => {
                      const linePlayers = lineupData.team.line_combinations.filter(p => p.line_id === lineId)
                      if (linePlayers.length === 0) return null

                      const formation = organizeByPosition(linePlayers)
                      const lineLabel = lineId.toUpperCase().replace('D', 'D-Pair ')

                      return (
                        <div key={lineId} className="line-row">
                          <h5 className="line-label">{lineLabel}</h5>
                          <div className="formation-row defense">
                            {['ld', 'rd'].map(pos => {
                              const player = formation[pos]
                              return (
                                <div key={pos} className="formation-player">
                                  {player ? (
                                    <>
                                      <div
                                        className="player-circle"
                                        style={{
                                          background: `linear-gradient(135deg, ${lineupData.team.primary_color} 0%, ${lineupData.team.secondary_color} 100%)`
                                        }}
                                      >
                                        {player.headshot_url ? (
                                          <img src={player.headshot_url} alt={player.player_name} className="player-headshot" />
                                        ) : (
                                          player.jersey_number || '?'
                                        )}
                                      </div>
                                      <div className="player-label">{player.player_name}</div>
                                    </>
                                  ) : (
                                    <>
                                      <div className="player-circle empty">—</div>
                                      <div className="player-label">Empty</div>
                                    </>
                                  )}
                                </div>
                              )
                            })}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              <div className="lineup-section">
                <h4>Goalies ({lineupData.team.goalies.length})</h4>
                <div className="lineup-grid">
                  {lineupData.team.goalies.map((player, idx) => (
                    <div key={idx} className="lineup-player">
                      <span className="player-number">#{player.jersey_number || '—'}</span>
                      <span className="player-name">{player.player_name}</span>
                      <span className="player-position">{player.position}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Opponent's Team Lineup */}
          {activeLineupTab === 'opponent' && lineupData.opponent && (
            <div className="team-lineup">
              <h3>{lineupData.opponent.team_name}</h3>
              {lineupData.opponent.opponent_name && (
                <p className="opponent-info">vs {lineupData.opponent.opponent_name}</p>
              )}

              {/* Hockey Formation Display for Opponent */}
              {selectedLine ? (
                // Show single line formation
                (() => {
                  const filteredPlayers = filterPlayersByLine(lineupData.opponent.line_combinations)

                  // Check if this is a special teams unit (PP or PK)
                  if (isSpecialTeams(selectedLine)) {
                    // Display special teams as a grid of skaters
                    return (
                      <div className="formation-container">
                        <div className="formation-row special-teams">
                          {filteredPlayers.map((player, idx) => (
                            <div key={idx} className="formation-player">
                              <div
                                className="player-circle"
                                style={{
                                  background: `linear-gradient(135deg, ${lineupData.opponent.primary_color} 0%, ${lineupData.opponent.secondary_color} 100%)`
                                }}
                              >
                                {player.headshot_url ? (
                                  <img src={player.headshot_url} alt={player.player_name} className="player-headshot" />
                                ) : (
                                  player.jersey_number || '?'
                                )}
                              </div>
                              <div className="player-label">{player.player_name}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )
                  }

                  // Regular 5v5 lines - organize by traditional positions
                  const formation = organizeByPosition(filteredPlayers)

                  return (
                    <div className="formation-container">
                      {/* Forwards */}
                      <div className="formation-row forwards">
                        {['lw', 'c', 'rw'].map(pos => {
                          const player = formation[pos]
                          return (
                            <div key={pos} className="formation-player">
                              {player ? (
                                <>
                                  <div
                                    className="player-circle"
                                    style={{
                                      background: `linear-gradient(135deg, ${lineupData.opponent.primary_color} 0%, ${lineupData.opponent.secondary_color} 100%)`
                                    }}
                                  >
                                    {player.headshot_url ? (
                                      <img src={player.headshot_url} alt={player.player_name} className="player-headshot" />
                                    ) : (
                                      player.jersey_number || '?'
                                    )}
                                  </div>
                                  <div className="player-label">{player.player_name}</div>
                                </>
                              ) : (
                                <>
                                  <div className="player-circle empty">—</div>
                                  <div className="player-label">Empty</div>
                                </>
                              )}
                            </div>
                          )
                        })}
                      </div>

                      {/* Defense */}
                      <div className="formation-row defense">
                        {['ld', 'rd'].map(pos => {
                          const player = formation[pos]
                          return (
                            <div key={pos} className="formation-player">
                              {player ? (
                                <>
                                  <div
                                    className="player-circle"
                                    style={{
                                      background: `linear-gradient(135deg, ${lineupData.opponent.primary_color} 0%, ${lineupData.opponent.secondary_color} 100%)`
                                    }}
                                  >
                                    {player.headshot_url ? (
                                      <img src={player.headshot_url} alt={player.player_name} className="player-headshot" />
                                    ) : (
                                      player.jersey_number || '?'
                                    )}
                                  </div>
                                  <div className="player-label">{player.player_name}</div>
                                </>
                              ) : (
                                <>
                                  <div className="player-circle empty">—</div>
                                  <div className="player-label">Empty</div>
                                </>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )
                })()
              ) : (
                // Show all lines stacked
                <div className="all-lines-container">
                  {/* Forward Lines Section */}
                  <div className="line-group">
                    {['f1', 'f2', 'f3', 'f4'].map(lineId => {
                      const linePlayers = lineupData.opponent.line_combinations.filter(p => p.line_id === lineId)
                      if (linePlayers.length === 0) return null

                      const formation = organizeByPosition(linePlayers)
                      const lineLabel = lineId.toUpperCase().replace('F', 'Line ')

                      return (
                        <div key={lineId} className="line-row">
                          <h5 className="line-label">{lineLabel}</h5>
                          <div className="formation-row forwards">
                            {['lw', 'c', 'rw'].map(pos => {
                              const player = formation[pos]
                              return (
                                <div key={pos} className="formation-player">
                                  {player ? (
                                    <>
                                      <div
                                        className="player-circle"
                                        style={{
                                          background: `linear-gradient(135deg, ${lineupData.opponent.primary_color} 0%, ${lineupData.opponent.secondary_color} 100%)`
                                        }}
                                      >
                                        {player.headshot_url ? (
                                          <img src={player.headshot_url} alt={player.player_name} className="player-headshot" />
                                        ) : (
                                          player.jersey_number || '?'
                                        )}
                                      </div>
                                      <div className="player-label">{player.player_name}</div>
                                    </>
                                  ) : (
                                    <>
                                      <div className="player-circle empty">—</div>
                                      <div className="player-label">Empty</div>
                                    </>
                                  )}
                                </div>
                              )
                            })}
                          </div>
                        </div>
                      )
                    })}
                  </div>

                  {/* Defense Pairs Section */}
                  <div className="line-group">
                    {['d1', 'd2', 'd3'].map(lineId => {
                      const linePlayers = lineupData.opponent.line_combinations.filter(p => p.line_id === lineId)
                      if (linePlayers.length === 0) return null

                      const formation = organizeByPosition(linePlayers)
                      const lineLabel = lineId.toUpperCase().replace('D', 'D-Pair ')

                      return (
                        <div key={lineId} className="line-row">
                          <h5 className="line-label">{lineLabel}</h5>
                          <div className="formation-row defense">
                            {['ld', 'rd'].map(pos => {
                              const player = formation[pos]
                              return (
                                <div key={pos} className="formation-player">
                                  {player ? (
                                    <>
                                      <div
                                        className="player-circle"
                                        style={{
                                          background: `linear-gradient(135deg, ${lineupData.opponent.primary_color} 0%, ${lineupData.opponent.secondary_color} 100%)`
                                        }}
                                      >
                                        {player.headshot_url ? (
                                          <img src={player.headshot_url} alt={player.player_name} className="player-headshot" />
                                        ) : (
                                          player.jersey_number || '?'
                                        )}
                                      </div>
                                      <div className="player-label">{player.player_name}</div>
                                    </>
                                  ) : (
                                    <>
                                      <div className="player-circle empty">—</div>
                                      <div className="player-label">Empty</div>
                                    </>
                                  )}
                                </div>
                              )
                            })}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              <div className="lineup-section">
                <h4>Goalies ({lineupData.opponent.goalies.length})</h4>
                <div className="lineup-grid">
                  {lineupData.opponent.goalies.map((player, idx) => (
                    <div key={idx} className="lineup-player">
                      <span className="player-number">#{player.jersey_number || '—'}</span>
                      <span className="player-name">{player.player_name}</span>
                      <span className="player-position">{player.position}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
          </div>
        )}

        {/* Injuries Content */}
        {activeMainTab === 'injuries' && (
          <div>
            {/* Player's Team Injuries */}
            <div className="injuries-team-section">
              <h3 className="injuries-title">{lineupData.team.team_name}</h3>
              {lineupData.team.injuries.length > 0 ? (
                <div className="injuries-grid">
                  {lineupData.team.injuries.map((player, idx) => (
                    <div key={idx} className="injury-card">
                      <div className="injury-card-header">
                        {player.headshot_url ? (
                          <div className="injury-player-headshot-container">
                            <img src={player.headshot_url} alt={player.player_name} className="injury-player-headshot" />
                          </div>
                        ) : (
                          <span className="player-number">#{player.jersey_number || '—'}</span>
                        )}
                        <span className="player-name">{player.player_name}</span>
                        <span className="player-position">{player.position}</span>
                      </div>
                      {player.injury_status && (
                        <div className="injury-card-status">
                          <span className="injury-status-badge">{player.injury_status}</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="no-injuries">
                  <p>No injuries or scratches reported</p>
                </div>
              )}
            </div>

            {/* Opponent's Team Injuries */}
            {lineupData.opponent && (
              <div className="injuries-team-section">
                <h3 className="injuries-title opponent">{lineupData.opponent.team_name}</h3>
                {lineupData.opponent.injuries.length > 0 ? (
                  <div className="injuries-grid">
                    {lineupData.opponent.injuries.map((player, idx) => (
                      <div key={idx} className="injury-card">
                        <div className="injury-card-header">
                          {player.headshot_url ? (
                            <div className="injury-player-headshot-container">
                              <img src={player.headshot_url} alt={player.player_name} className="injury-player-headshot" />
                            </div>
                          ) : (
                            <span className="player-number">#{player.jersey_number || '—'}</span>
                          )}
                          <span className="player-name">{player.player_name}</span>
                          <span className="player-position">{player.position}</span>
                        </div>
                        {player.injury_status && (
                          <div className="injury-card-status">
                            <span className="injury-status-badge">{player.injury_status}</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="no-injuries">
                    <p>No injuries or scratches reported</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default PlayerLineups