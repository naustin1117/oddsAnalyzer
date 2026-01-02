import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Player from './pages/Player'
import About from './pages/About'
import Login from './pages/Login'
import Sidebar from './components/common/Sidebar'

function App() {
  return (
    <>
      <Sidebar />
      <div style={{ marginLeft: '60px' }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<Login />} />
          <Route path="/player/:playerId" element={<Player />} />
        </Routes>
      </div>
    </>
  )
}

export default App