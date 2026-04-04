import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Session } from '../services/types';
import { FileUp, FileText, CheckCircle, AlertTriangle, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
  const { user } = useAuth();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const data = await api.getSessions();
      setSessions(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const getStatusClass = (status: string) => {
    if (status === 'Processing') return 'processing';
    if (status === 'Requires Attention') return 'attention';
    return 'clean'; // Clean or Ready to Send
  };

  const activeErrors = sessions.reduce((acc, s) => acc + s.errors.length, 0);

  return (
    <div className="dashboard-page">
      <div className="dash-header">
        <h1 className="dash-title">Welcome back, {user?.name.split(' ')[0]}</h1>
        <p className="dash-subtitle">Here's the status of your EDI pipeline today.</p>
      </div>

      {/* Stats Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '24px', marginBottom: '40px' }}>
        <div className="dash-card" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ background: 'rgba(0, 80, 255, 0.1)', padding: '16px', borderRadius: '12px', color: '#0050FF' }}>
            <FileText size={24} />
          </div>
          <div>
            <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--text-primary)' }}>{sessions.length}</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Total Session{sessions.length !== 1 ? 's' : ''}</div>
          </div>
        </div>
        
        <div className="dash-card" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ background: 'rgba(255, 149, 0, 0.1)', padding: '16px', borderRadius: '12px', color: '#FF9500' }}>
            <AlertTriangle size={24} />
          </div>
          <div>
            <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--text-primary)' }}>{activeErrors}</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Active Errors</div>
          </div>
        </div>

        <div className="dash-card" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ background: 'rgba(52, 199, 89, 0.1)', padding: '16px', borderRadius: '12px', color: '#34C759' }}>
            <CheckCircle size={24} />
          </div>
          <div>
            <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--text-primary)' }}>98%</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Success Rate</div>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        {/* Recent Sessions */}
        <div className="dash-card">
          <div className="card-header-flex">
            <h3 className="card-title">Recent Uploads</h3>
            <button className="btn" style={{ fontSize: '0.875rem', padding: '6px 12px', background: 'var(--surface-3)', color: 'var(--text-primary)' }}>View All</button>
          </div>
          
          {loading ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>Loading sessions...</div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>File Name</th>
                    <th>Date</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.slice(0, 5).map(session => (
                    <tr key={session.id}>
                      <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{session.filename}</td>
                      <td>{new Date(session.uploadDate).toLocaleString()}</td>
                      <td>
                        <span className={`status-badge ${getStatusClass(session.status)}`}>
                          {session.status}
                        </span>
                      </td>
                      <td>
                        <button 
                          className="btn" 
                          style={{ padding: '6px 12px', background: 'var(--surface-4)', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}
                          onClick={() => navigate(`/dashboard/session/${session.id}`)}
                        >
                          View <ArrowRight size={14} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Quick Upload */}
        <div className="dash-card" style={{ display: 'flex', flexDirection: 'column' }}>
          <h3 className="card-title" style={{ marginBottom: '16px' }}>Quick Upload</h3>
          <div 
            style={{ 
              flex: 1, 
              border: '2px dashed var(--surface-border)', 
              borderRadius: '12px', 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: 'center', 
              justifyContent: 'center',
              padding: '40px 20px',
              textAlign: 'center',
              background: 'var(--surface-2)',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => e.currentTarget.style.borderColor = 'rgba(0,214,255,0.5)'}
            onMouseOut={(e) => e.currentTarget.style.borderColor = 'var(--surface-border)'}
            onClick={() => navigate('/dashboard/upload')}
          >
            <div style={{ background: 'var(--surface-3)', padding: '16px', borderRadius: '50%', marginBottom: '16px' }}>
              <FileUp size={32} color="#00D6FF" />
            </div>
            <h4 style={{ color: 'var(--text-primary)', marginBottom: '8px' }}>Drag & Drop EDI File</h4>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Supports .edi, .x12, .txt</p>
          </div>
        </div>
      </div>
    </div>
  );
}
