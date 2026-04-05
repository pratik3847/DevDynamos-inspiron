import { Session } from '../../services/types';
import { DownloadCloud, FileJson, FileText, CheckCircle } from 'lucide-react';
import { api } from '../../services/api';

export default function DownloadPanel({ session }: { session: Session }) {
  const isClean = session.status === 'Clean' || session.status === 'Ready to Send';

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ textAlign: 'center', marginBottom: '40px', maxWidth: '500px' }}>
        {isClean ? (
          <>
            <div style={{ background: 'rgba(52, 199, 89, 0.1)', width: '80px', height: '80px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 24px' }}>
              <CheckCircle size={40} color="#34C759" />
            </div>
            <h2 style={{ fontSize: '2rem', fontWeight: 700, color: '#fff', marginBottom: '16px' }}>Ready for Transmission</h2>
            <p style={{ color: 'var(--text-secondary)' }}>All required SNIP validation checks passed. This file has been regenerated with the accepted fixes and is ready to send to the clearinghouse.</p>
          </>
        ) : (
          <>
             <h2 style={{ fontSize: '2rem', fontWeight: 700, color: '#fff', marginBottom: '16px' }}>Downloads & Reports</h2>
             <p style={{ color: 'var(--text-secondary)' }}>You can download the current parsed data or an audit report. Fix pending errors to unlock the final clean EDI file.</p>
          </>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '24px', width: '100%', maxWidth: '900px' }}>
        {/* Corrected EDI */}
        <div className="dash-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
           <div style={{ background: 'rgba(0, 80, 255, 0.1)', padding: '16px', borderRadius: '50%', marginBottom: '16px' }}>
              <DownloadCloud size={32} color="#0050FF" />
           </div>
           <h3 style={{ color: '#fff', fontSize: '1.125rem', marginBottom: '8px' }}>Corrected EDI</h3>
           <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '24px' }}>Current X12 payload (corrected if fixes were applied)</p>
           <button
             className="btn btn-primary"
             style={{ width: '100%' }}
             onClick={() => api.downloadSessionEdi(session.id)}
           >
             Download .edi
           </button>
        </div>

        {/* JSON Export */}
        <div className="dash-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
           <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '16px', borderRadius: '50%', marginBottom: '16px' }}>
              <FileJson size={32} color="#fff" />
           </div>
           <h3 style={{ color: '#fff', fontSize: '1.125rem', marginBottom: '8px' }}>Parsed JSON</h3>
           <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '24px' }}>Hierarchical data mapping</p>
           <button
             className="btn"
             style={{ width: '100%', border: '1px solid rgba(255,255,255,0.2)', color: '#fff' }}
             onClick={() => api.downloadSessionJson(session.id)}
           >
             Download .json
           </button>
        </div>

        {/* Audit Report */}
        <div className="dash-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
           <div style={{ background: 'rgba(255, 149, 0, 0.1)', padding: '16px', borderRadius: '50%', marginBottom: '16px' }}>
              <FileText size={32} color="#FF9500" />
           </div>
           <h3 style={{ color: '#fff', fontSize: '1.125rem', marginBottom: '8px' }}>Audit Log</h3>
           <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '24px' }}>Original errors & applied fixes</p>
           <button
             className="btn"
             style={{ width: '100%', border: '1px solid rgba(255,255,255,0.2)', color: '#fff' }}
             onClick={() => api.downloadSessionReport(session.id)}
           >
             Download .json
           </button>
        </div>
      </div>
    </div>
  );
}
