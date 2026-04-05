import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { isAuthenticated, user } = useAuth();

  return (
    <nav className="navbar" id="navbar">
      <div className="nav-container">
        <div className="nav-brand">Health EDI</div>
        <div className="nav-links">
          <Link to="/">Overview</Link>
          <a href="/#solution">Workflow</a>
          <a href="/#validation">Validation</a>
          <a href="/#agents">AI Agents</a>
        </div>
        <div className="nav-actions" style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          {isAuthenticated ? (
            <>
              <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>{user?.name}</span>
              <Link to="/dashboard" className="btn btn-primary">Dashboard</Link>
            </>
          ) : (
            <>
              <Link to="/login" className="btn" style={{ color: '#fff' }}>Log In</Link>
              <Link to="/signup" className="btn btn-primary">Sign Up</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
