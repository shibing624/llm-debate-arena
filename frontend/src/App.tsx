import { Routes, Route } from 'react-router-dom'
import Arena from './pages/Arena'
import Leaderboard from './pages/Leaderboard'
import MatchShare from './pages/MatchShare'
import Login from './pages/Login'
import Register from './pages/Register'

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* 路由 - 无导航栏，主页自带侧边栏 */}
      <Routes>
        <Route path="/" element={<Arena />} />
        <Route path="/leaderboard" element={<Leaderboard />} />
        <Route path="/match/:matchId" element={<MatchShare />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Routes>
    </div>
  )
}

export default App
