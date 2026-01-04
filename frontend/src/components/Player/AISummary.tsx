import { useEffect, useState } from 'react'
import './AISummary.css'

interface AISummaryProps {
  summary: string
}

function AISummary({ summary }: AISummaryProps) {
  const [revealedIndex, setRevealedIndex] = useState(0)
  const isTyping = revealedIndex < summary.length

  useEffect(() => {
    let currentIndex = 0
    const typingSpeed = 20 // milliseconds per character

    const typeNextCharacter = () => {
      if (currentIndex < summary.length) {
        setRevealedIndex(currentIndex + 1)
        currentIndex++
        setTimeout(typeNextCharacter, typingSpeed)
      }
    }

    // Wait 1.5 seconds before starting the animation
    setTimeout(() => {
      typeNextCharacter()
    }, 1500)
  }, [summary])

  return (
    <div className="ai-summary-container">
      <div className="ai-summary-header">
        <span className="ai-badge">
          {isTyping && <span className="spinner"></span>}
          AI Analysis
        </span>
      </div>
      <p className="ai-summary-text">
        {summary.split('').map((char, index) => (
          <span
            key={index}
            className={index < revealedIndex ? 'revealed' : 'hidden-char'}
          >
            {char}
          </span>
        ))}
      </p>
    </div>
  )
}

export default AISummary