import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle2, AlertCircle, FileText, Code2, AlertTriangle, FileUp, MessageSquare, Download } from 'lucide-react';
import { api } from '../services/api';
import { Session } from '../services/types';

// We will import panels here
import RawViewer from '../components/dashboard/RawViewer';
import ParsedJsonViewer from '../components/dashboard/ParsedJsonViewer';
import ValidationPanel from '../components/dashboard/ValidationPanel';
import FixPanel from '../components/dashboard/FixPanel';
import AIChatPanel from '../components/dashboard/AIChatPanel';
import DownloadPanel from '../components/dashboard/DownloadPanel';

const TABS = [
  { id: 'raw', label: 'Upload & Raw', icon: <FileText size={16} /> },
  { id: 'parsed', label: 'Parsed JSON', icon: <Code2 size={16} /> },
  { id: 'validation', label: 'Validation', icon: <AlertTriangle size={16} /> },
  { id: 'fixes', label: 'Fix Suggestions', icon: <FileUp size={16} /> }, // using FileUp as a placeholder fix icon
  { id: 'chat', label: 'AI Chat', icon: <MessageSquare size={16} /> },
  { id: 'download', label: 'Download', icon: <Download size={16} /> },
];

export default function SessionDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('validation'); // start here if errors exist

  useEffect(() => {
    if (id) {
      loadSession(id);
    }
  }, [id]);

  const loadSession = async (sessionId: string) => {
    try {
      const data = await api.getSession(sessionId);
      if (data) {
        setSession(data);
        if (data.errors.length === 0) {
          setActiveTab('download');
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div style={{ padding: '40px', color: '#fff' }}>Loading session...</div>;
  }

  if (!session) {
    return <div style={{ padding: '40px', color: '#fff' }}>Session not found.</div>;
  }

  const isClean = session.status === 'Clean' || session.status === 'Ready to Send';

  return (
    <div className="session-detail">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '32px' }}>
        <button 
          onClick={() => navigate('/dashboard')}
          style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
        >
          <ArrowLeft size={20} />
        </button>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <h2 style={{ fontSize: '1.5rem', color: '#fff', fontWeight: 600 }}>{session.filename}</h2>
            <span className={`status-badge ${isClean ? 'clean' : 'attention'}`}>
              {isClean ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
              {session.status}
            </span>
          </div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginTop: '4px' }}>
            ID: {session.id} &bull; Uploaded {new Date(session.uploadDate).toLocaleString()}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', marginBottom: '24px', display: 'flex', gap: '24px', overflowX: 'auto', paddingBottom: '1px' }}>
        {TABS.map(tab => (
          <div 
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '12px 0',
              color: activeTab === tab.id ? '#fff' : 'var(--text-secondary)',
              borderBottom: `2px solid ${activeTab === tab.id ? 'var(--accent-blue)' : 'transparent'}`,
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '0.875rem',
              fontWeight: 500,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'all 0.2s'
            }}
          >
            {tab.icon}
            {tab.label}
            {tab.id === 'validation' && session.errors.length > 0 && (
              <span style={{ background: 'rgba(255,59,48,0.2)', color: '#ff6b6b', padding: '2px 6px', borderRadius: '99px', fontSize: '0.75rem' }}>
                {session.errors.length}
              </span>
            )}
            {tab.id === 'fixes' && session.fixes.filter(f => f.status === 'pending').length > 0 && (
              <span style={{ background: 'rgba(0,214,255,0.2)', color: '#80EEFF', padding: '2px 6px', borderRadius: '99px', fontSize: '0.75rem' }}>
                {session.fixes.filter(f => f.status === 'pending').length}
              </span>
            )}
          </div>
        ))}
      </div>

      {/* Content Area */}
      <div className="dash-card" style={{ minHeight: '500px' }}>
        {activeTab === 'raw' && <RawViewer rawEdi={session.rawEdi} />}
        {activeTab === 'parsed' && <ParsedJsonViewer parsedJson={session.parsedJson} />}
        {activeTab === 'validation' && <ValidationPanel errors={session.errors} />}
        {activeTab === 'fixes' && <FixPanel session={session} onFixApplied={() => loadSession(session.id)} />}
        {activeTab === 'chat' && <AIChatPanel session={session} />}
        {activeTab === 'download' && <DownloadPanel session={session} />}
      </div>
    </div>
  );
}
