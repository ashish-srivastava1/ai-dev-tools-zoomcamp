import { NavLink, Route, Routes } from 'react-router-dom';
import HostDashboard from './pages/HostDashboard';
import PublicStatus from './pages/PublicStatus';
import './App.css';

export default function App() {
  return (
    <>
      <header className="app-header">
        <div className="app-header-inner">
          <span className="app-title">TableTurn</span>
          <nav className="app-nav">
            <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : undefined)}>
              Host dashboard
            </NavLink>
            <NavLink to="/status" className={({ isActive }) => (isActive ? 'active' : undefined)}>
              Check my status
            </NavLink>
          </nav>
        </div>
      </header>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<HostDashboard />} />
          <Route path="/status" element={<PublicStatus />} />
        </Routes>
      </main>
    </>
  );
}
