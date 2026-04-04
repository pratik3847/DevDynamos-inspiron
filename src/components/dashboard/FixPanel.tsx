import React, { useState } from 'react';
import { Session } from '../../services/types';
import { api } from '../../services/api';
import { Check, X, ArrowDown } from 'lucide-react';

interface FixPanelProps {
  session: Session;
  onFixApplied: () => void;
}

export default function FixPanel({ session, onFixApplied }: FixPanelProps) {
  const [processing, setProcessing] = useState<string | null>(null);
  
  const pendingFixes = session.fixes.filter(f => f.status === 'pending');
  const acceptedFixes = session.fixes.filter(f => f.status === 'accepted');

  const handleAccept = async (fix: Session['fixes'][number]) => {
    setProcessing(fix.id);
    try {
      await api.applyFix(session.id, fix);
      onFixApplied();
    } catch (e) {
      console.error(e);
    } finally {
      setProcessing(null);
    }
  };

  const handleAcceptAll = async () => {
    if (pendingFixes.length === 0) return;
    setProcessing('BATCH');
    try {
      await api.applyFixBatch(session.id, pendingFixes);
      onFixApplied();
    } catch (e) {
      console.error(e);
    } finally {
      setProcessing(null);
    }
  };

  if (session.fixes.length === 0) {
    return (
      <div style={{ padding: '60px 0', textAlign: 'center', color: 'var(--text-secondary)' }}>
        No fixes required for this file.
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
         <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: '#fff' }}>Suggested Corrections</h3>
         {pendingFixes.length > 0 && (
           <button
             className="btn btn-primary"
             style={{ padding: '8px 16px', fontSize: '0.875rem' }}
             onClick={handleAcceptAll}
             disabled={processing === 'BATCH'}
           >
             Accept All Pending ({pendingFixes.length})
           </button>
         )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {session.fixes.map(fix => {
          const isAccepted = fix.status === 'accepted';
          
          return (
            <div key={fix.id} className="fix-ui" style={{ margin: 0, maxWidth: '100%', opacity: isAccepted ? 0.6 : 1, border: isAccepted ? '1px solid rgba(52, 199, 89, 0.3)' : '1px solid rgba(255,255,255,0.1)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '24px' }}>
                <div style={{ color: '#fff', fontWeight: 500 }}>{fix.description}</div>
                {isAccepted && <div style={{ color: '#34C759', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.875rem', fontWeight: 600 }}><Check size={16} /> Applied</div>}
              </div>

              <div className="fix-row" style={{ background: 'rgba(0,0,0,0.3)', padding: '24px', borderRadius: '12px' }}>
                <div className="original" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Original:</span>
                  <span className="strike">{fix.original}</span>
                </div>
                <div className="arrow"><ArrowDown size={20} /></div>
                <div className="suggested" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>suggested:</span>
                  <span className="highlight-green">{fix.suggested}</span>
                </div>
              </div>

              {!isAccepted && (
                <div className="fix-meta" style={{ marginTop: '24px' }}>
                  <span className={`confidence ${fix.confidence.toLowerCase()}`} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                     <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: fix.confidence === 'High' ? '#34C759' : '#FF9500' }}></span>
                     {fix.confidence} Confidence Fix
                  </span>
                  <div style={{ display: 'flex', gap: '12px' }}>
                    <button className="btn" style={{ border: '1px solid rgba(255,255,255,0.2)', color: '#fff', padding: '8px 16px', fontSize: '0.875rem' }}>Reject</button>
                    <button
                      className="btn btn-accept"
                      style={{ padding: '8px 24px', fontSize: '0.875rem' }}
                      onClick={() => handleAccept(fix)}
                      disabled={!fix.id || processing === fix.id}
                    >
                      {processing === fix.id ? 'Applying...' : 'Accept Fix'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
