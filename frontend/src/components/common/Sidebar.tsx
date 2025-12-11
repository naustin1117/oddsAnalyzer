import { useNavigate, useLocation } from 'react-router-dom'
import { Home, Info, Settings, Circle } from 'lucide-react'
import './Sidebar.css'

function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <div className="sidebar">
      <div className="sidebar-logo">
        <Circle size={28} />
      </div>

      <div className="sidebar-content">
        <button
          className={`sidebar-item ${location.pathname === '/' ? 'active' : ''}`}
          onClick={() => navigate('/')}
          title="Home"
        >
          <Home size={20} />
        </button>

        <button
          className={`sidebar-item ${location.pathname === '/about' ? 'active' : ''}`}
          onClick={() => navigate('/about')}
          title="Information"
        >
          <Info size={20} />
        </button>
      </div>

      <div className="sidebar-footer">
        <button
          className="sidebar-item"
          title="Settings"
        >
          <Settings size={20} />
        </button>
      </div>
    </div>
  )
}

export default Sidebar