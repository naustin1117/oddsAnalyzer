import './About.css'

function About() {
  return (
    <div className="App">
      <div className="about-container">
        <h1>About NHL Odds Analyzer</h1>

        <section className="about-section">
          <h2>What is this?</h2>
          <p>
            NHL Odds Analyzer is a data-driven platform that provides daily predictions for NHL player prop bets,
            specifically focusing on shots on goal. Using historical performance data, advanced statistics, and
            machine learning models, we analyze matchups to identify value betting opportunities.
          </p>
        </section>

        <section className="about-section">
          <h2>How it works</h2>
          <p>
            Our prediction system analyzes multiple factors for each player and matchup:
          </p>
          <ul>
            <li><strong>Recent Performance:</strong> Player's shot totals over the last 10 games</li>
            <li><strong>Season Averages:</strong> Overall statistical trends and consistency</li>
            <li><strong>Matchup Data:</strong> Opponent defensive statistics and historical matchups</li>
            <li><strong>Line Assignments:</strong> Ice time and power play opportunities based on daily lineups</li>
            <li><strong>Vegas Lines:</strong> Sportsbook odds and implied probabilities</li>
          </ul>
          <p>
            The model processes this data to generate a predicted shot total for each player, which is then
            compared against the betting line to identify potential edges.
          </p>
        </section>

        <section className="about-section">
          <h2>Understanding Predictions</h2>
          <div className="confidence-explainer">
            <div className="confidence-item">
              <span className="confidence-badge-about high">HIGH</span>
              <p>Strong statistical edge with significant deviation from the line. These represent our most confident predictions.</p>
            </div>
            <div className="confidence-item">
              <span className="confidence-badge-about medium">MEDIUM</span>
              <p>Moderate edge with favorable indicators. Good value plays with solid supporting data.</p>
            </div>
            <div className="confidence-item">
              <span className="confidence-badge-about low">LOW</span>
              <p>Smaller edge or less certain prediction. May still provide value but with higher variance.</p>
            </div>
          </div>
        </section>

        <section className="about-section">
          <h2>Features</h2>
          <ul>
            <li><strong>Daily Predictions:</strong> Updated predictions for all games with available lines</li>
            <li><strong>Player Insights:</strong> Detailed stats, charts, and recent performance for each player</li>
            <li><strong>Live Lineups:</strong> Real-time lineup data including line combinations and injuries</li>
            <li><strong>Performance Tracking:</strong> Historical record of prediction accuracy and ROI</li>
            <li><strong>Confidence Filtering:</strong> Focus on high-confidence plays or explore all predictions</li>
          </ul>
        </section>

        <section className="about-section">
          <h2>Using the Platform</h2>
          <ol>
            <li><strong>Browse Predictions:</strong> The home page shows all available predictions for today's games</li>
            <li><strong>Filter by Confidence:</strong> Use the filter buttons to view only high, medium, or low confidence picks</li>
            <li><strong>Click for Details:</strong> Click any prediction to see detailed player statistics, recent games, and lineup information</li>
            <li><strong>Check the Record:</strong> View the historical performance in the sidebar to understand model accuracy</li>
            <li><strong>Make Informed Decisions:</strong> Use our predictions as one input in your betting research</li>
          </ol>
        </section>

        <section className="about-section disclaimer">
          <h2>Disclaimer</h2>
          <p>
            This tool is for informational and entertainment purposes only. Sports betting involves risk,
            and past performance does not guarantee future results. Always bet responsibly and within your means.
            This is not financial advice.
          </p>
        </section>
      </div>
    </div>
  )
}

export default About