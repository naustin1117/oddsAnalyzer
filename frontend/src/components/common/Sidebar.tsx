import { useNavigate, useLocation } from 'react-router-dom'
import { Home, Info, Settings, Circle, User, LogOut } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import './Sidebar.css'

function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, signOut } = useAuth()

  const handleSignOut = async () => {
    try {
      await signOut()
      navigate('/login')
    } catch (error) {
      console.error('Error signing out:', error)
    }
  }

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
        {user ? (
          <>
            <button
              className="sidebar-item"
              onClick={() => navigate('/settings')}
              title="Settings"
            >
              <Settings size={20} />
            </button>
            <button
              className="sidebar-item"
              onClick={handleSignOut}
              title="Sign Out"
            >
              <LogOut size={20} />
            </button>
          </>
        ) : (
          <button
            className={`sidebar-item ${location.pathname === '/login' ? 'active' : ''}`}
            onClick={() => navigate('/login')}
            title="Sign In"
          >
            <User size={20} />
          </button>
        )}
      </div>
    </div>
  )
}

export default Sidebar