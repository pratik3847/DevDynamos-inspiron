import React, { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { api } from '../services/api'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  
  const navigate = useNavigate()
  const location = useLocation()
  const { loginState } = useAuth()
  
  const from = location.state?.from?.pathname || '/dashboard'

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    
    try {
      const user = await api.login(email, password)
      loginState(user)
      navigate(from, { replace: true })
    } catch (err: any) {
      setError(err.message || 'Failed to log in')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', paddingTop: '72px' }}>
      <div style={{
        background: 'rgba(10, 10, 12, 0.6)',
        backdropFilter: 'blur(24px)',
        WebkitBackdropFilter: 'blur(24px)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '20px',
        padding: '40px',
        width: '100%',
        maxWidth: '420px',
        textAlign: 'center',
        boxShadow: '0 30px 60px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.1)'
      }}>
        <h2 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '8px' }}>Welcome Back</h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '32px' }}>Log in to your EDI intelligence portal.</p>
        
        {error && <div style={{ background: 'rgba(255,59,48,0.1)', color: '#FF3B30', padding: '12px', borderRadius: '8px', marginBottom: '16px', fontSize: '0.875rem' }}>{error}</div>}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <input 
            type="email" 
            placeholder="Email address" 
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
            style={{ width: '100%', padding: '12px 16px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.2)', background: 'rgba(0,0,0,0.2)', color: 'white', outline: 'none' }} 
          />
          <input 
            type="password" 
            placeholder="Password" 
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            style={{ width: '100%', padding: '12px 16px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.2)', background: 'rgba(0,0,0,0.2)', color: 'white', outline: 'none' }} 
          />
          <button type="submit" disabled={loading} className="btn btn-primary" style={{ width: '100%', padding: '14px', marginTop: '16px', opacity: loading ? 0.7 : 1 }}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p style={{ marginTop: '24px', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
          Don't have an account? <Link to="/signup" style={{ color: '#fff', textDecoration: 'none' }}>Sign up</Link>
        </p>
      </div>
    </div>
  )
}
