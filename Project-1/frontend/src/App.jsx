import { NavLink, Route, Routes } from 'react-router-dom'
import DashboardPage from './pages/DashboardPage'
import TracksPage from './pages/TracksPage'
import SessionsPage from './pages/SessionsPage'
import SettingsPage from './pages/SettingsPage'

const NAV = [
  ['/', 'Dashboard'],
  ['/tracks', 'Tracks'],
  ['/sessions', 'Sessions'],
  ['/settings', 'Settings'],
]

export default function App() {
  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <img src="/favicon.svg" alt="" width="24" height="24" />
          <span>LearnLoop</span>
        </div>
        <nav aria-label="Main">
          {NAV.map(([to, label]) => (
            <NavLink key={to} to={to} end={to === '/'}>
              {label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/tracks" element={<TracksPage />} />
          <Route path="/sessions" element={<SessionsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<p>Page not found.</p>} />
        </Routes>
      </main>
    </div>
  )
}
