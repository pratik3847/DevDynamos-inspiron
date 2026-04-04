import React from 'react';
import { FileText, CheckCircle, AlertTriangle, Clock, UploadCloud, CheckSquare, Wrench, Download } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function DashboardHome() {
  const navigate = useNavigate();

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '8px' }}>Dashboard</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '32px' }}>Monitor your EDI processing pipeline and system health</p>

      {/* Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '24px', marginBottom: '24px' }}>
        <div className="dash-card">
          <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: 'rgba(0, 80, 255, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
            <FileText size={20} color="#0050FF" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '4px' }}>12</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Files Processed</div>
        </div>
        
        <div className="dash-card">
          <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: 'rgba(52, 199, 89, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
            <CheckCircle size={20} color="#34C759" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '4px' }}>78.5%</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Validation Success</div>
        </div>

        <div className="dash-card">
          <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: 'rgba(255, 149, 0, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
            <AlertTriangle size={20} color="#FF9500" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '4px' }}>43</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Errors Found</div>
        </div>

        <div className="dash-card">
          <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: 'rgba(0, 214, 255, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
            <Clock size={20} color="#00D6FF" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '4px' }}>1.2s</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Avg. Process Time</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        {/* Chart View (Mocked) */}
        <div className="dash-card" style={{ display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '24px' }}>Processing Overview</h3>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)', fontSize: '0.875rem', minHeight: '300px' }}>
            Upload files to see processing trends.
          </div>
        </div>

        {/* Quick Actions */}
        <div className="dash-card">
          <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '24px' }}>Quick Actions</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div 
              onClick={() => navigate('/dashboard/upload')}
              style={{ display: 'flex', alignItems: 'center', gap: '16px', background: 'rgba(0, 80, 255, 0.05)', padding: '16px', borderRadius: '12px', cursor: 'pointer', border: '1px solid rgba(0, 80, 255, 0.1)' }}
            >
              <div style={{ background: 'rgba(0, 80, 255, 0.1)', padding: '8px', borderRadius: '8px' }}><UploadCloud size={16} color="#0050FF" /></div>
              <div style={{ flex: 1 }}>
                 <div style={{ fontWeight: 600, fontSize: '0.9375rem' }}>Upload Files</div>
                 <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Import EDI files for processing</div>
              </div>
            </div>

            <div 
              onClick={() => navigate('/dashboard/validation')}
              style={{ display: 'flex', alignItems: 'center', gap: '16px', background: 'rgba(52, 199, 89, 0.05)', padding: '16px', borderRadius: '12px', cursor: 'pointer', border: '1px solid rgba(52, 199, 89, 0.1)' }}
            >
              <div style={{ background: 'rgba(52, 199, 89, 0.1)', padding: '8px', borderRadius: '8px' }}><CheckSquare size={16} color="#34C759" /></div>
              <div style={{ flex: 1 }}>
                 <div style={{ fontWeight: 600, fontSize: '0.9375rem' }}>Validate Files</div>
                 <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Check files against rules</div>
              </div>
            </div>
            
            <div 
              onClick={() => navigate('/dashboard/fix-assistant')}
              style={{ display: 'flex', alignItems: 'center', gap: '16px', background: 'rgba(255, 149, 0, 0.05)', padding: '16px', borderRadius: '12px', cursor: 'pointer', border: '1px solid rgba(255, 149, 0, 0.1)' }}
            >
              <div style={{ background: 'rgba(255, 149, 0, 0.1)', padding: '8px', borderRadius: '8px' }}><Wrench size={16} color="#FF9500" /></div>
              <div style={{ flex: 1 }}>
                 <div style={{ fontWeight: 600, fontSize: '0.9375rem' }}>Fix Errors</div>
                 <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Auto-correct validation issues</div>
              </div>
            </div>

            <div 
              style={{ display: 'flex', alignItems: 'center', gap: '16px', background: 'rgba(0, 214, 255, 0.05)', padding: '16px', borderRadius: '12px', cursor: 'pointer', border: '1px solid rgba(0, 214, 255, 0.1)' }}
            >
              <div style={{ background: 'rgba(0, 214, 255, 0.1)', padding: '8px', borderRadius: '8px' }}><Download size={16} color="#00D6FF" /></div>
              <div style={{ flex: 1 }}>
                 <div style={{ fontWeight: 600, fontSize: '0.9375rem' }}>Export Data</div>
                 <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Download processed files</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
