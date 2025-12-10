import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Player from './pages/Player'
import Sidebar from './components/common/Sidebar'

function App() {
  return (
    <>
      <Sidebar />
      <div style={{ marginLeft: '60px' }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/player/:playerId" element={<Player />} />
        </Routes>
      </div>
    </>
  )
}

export default App