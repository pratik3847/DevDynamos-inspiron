import React, { useState } from 'react';
import { Play, CheckCircle2, AlertTriangle, AlertCircle, RefreshCw, ChevronDown, ChevronRight, FileCode, Wrench, FileText } from 'lucide-react';
import { useSession } from '../context/SessionContext';

export default function ValidationEngine() {
  const { activeSession, isLoading, refreshSession } = useSession();
  const [expandedNodes, setExpandedNodes] = useState<Record<string, boolean>>({});
  const [activeFilter, setActiveFilter] = useState<'all' | 'errors' | 'warnings'>('all');

  const toggleNode = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setExpandedNodes(prev => ({ ...prev, [id]: !prev[id] }));
  };

  if (!activeSession) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-secondary)' }}>
         <FileText size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
         <h3>No Active Session</h3>
         <p>Please upload a file to view validation results.</p>
      </div>
    );
  }

  // Derived metrics
  const totalSegments = activeSession.parsedJson?.segments?.length || 0;
  const uploadedIssues = activeSession.originalErrors || activeSession.errors || [];
  const errors = uploadedIssues.filter(e => e.severity === 'Error' || e.severity === 'Critical');
  const warnings = uploadedIssues.filter(e => e.severity === 'Warning');
  const filteredIssues = activeFilter === 'errors' ? errors : activeFilter === 'warnings' ? warnings : uploadedIssues;
  const segmentsWithIssues = new Set(uploadedIssues.map(e => e.segment));
  const validSegments = totalSegments - segmentsWithIssues.size;
  const healthScore = totalSegments > 0 ? Math.round((validSegments / totalSegments) * 100) : 100;

  return (
    <div className="edi-page">
      <div className="edi-page__header">
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '8px' }}>Validation Engine</h1>
          <p style={{ color: 'var(--text-secondary)' }}>Validate EDI files against HIPAA and custom rules</p>
        </div>
        <button className="btn outline" style={{ display: 'flex', alignItems: 'center', gap: '8px' }} onClick={refreshSession}>
           <Play size={16} /> Re-Calculate
        </button>
      </div>

      {isLoading ? (
         <div style={{ padding: '20px', color: 'var(--text-secondary)' }}>Loading Validation Metrics...</div>
      ) : (
        <>
          <div className="dash-card" style={{ marginBottom: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: errors.length > 0 ? 'rgba(255, 59, 48, 0.1)' : 'rgba(52, 199, 89, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  {errors.length > 0 ? <AlertCircle size={24} color="#FF3B30" /> : <CheckCircle2 size={24} color="#34C759" />}
                </div>
                <div>
                  <div style={{ fontSize: '1.125rem', fontWeight: 600 }}>Validation Complete</div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>{activeSession.filename}</div>
                </div>
              </div>
              <button className="btn outline" style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 12px' }} onClick={refreshSession}>
                 <RefreshCw size={14} /> Re-validate
              </button>
            </div>

            <div style={{ marginBottom: '8px', display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Validation Health</span>
              <span style={{ fontWeight: 600, color: healthScore < 100 ? '#FF3B30' : '#34C759' }}>{healthScore}%</span>
            </div>
            <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
              <div style={{ width: `${healthScore}%`, height: '100%', background: healthScore < 100 ? '#FF3B30' : '#34C759', borderRadius: '3px', transition: 'width 1s ease' }}></div>
            </div>
          </div>

          <div className="edi-grid edi-grid--4" style={{ marginBottom: '24px' }}>
            <div className="dash-card" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
               <FileCode size={24} color="#0050FF" />
               <div>
                 <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{totalSegments}</div>
                 <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Total Segments</div>
               </div>
            </div>
            <div className="dash-card" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
               <CheckCircle2 size={24} color="#34C759" />
               <div>
                 <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{validSegments}</div>
                 <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Valid</div>
               </div>
            </div>
            <div className="dash-card" style={{ display: 'flex', alignItems: 'center', gap: '16px', background: errors.length > 0 ? 'rgba(255, 59, 48, 0.05)' : 'var(--bg-card)', border: errors.length > 0 ? '1px solid rgba(255, 59, 48, 0.1)' : '1px solid rgba(255,255,255,0.05)' }}>
               <AlertCircle size={24} color={errors.length > 0 ? '#FF3B30' : 'var(--text-secondary)'} />
               <div>
                 <div style={{ fontSize: '1.5rem', fontWeight: 700, color: errors.length > 0 ? '#FF3B30' : 'var(--text-secondary)' }}>{errors.length}</div>
                 <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Errors</div>
               </div>
            </div>
            <div className="dash-card" style={{ display: 'flex', alignItems: 'center', gap: '16px', background: warnings.length > 0 ? 'rgba(255, 149, 0, 0.05)' : 'var(--bg-card)', border: warnings.length > 0 ? '1px solid rgba(255, 149, 0, 0.1)' : '1px solid rgba(255,255,255,0.05)' }}>
               <AlertTriangle size={24} color={warnings.length > 0 ? '#FF9500' : 'var(--text-secondary)'} />
               <div>
                 <div style={{ fontSize: '1.5rem', fontWeight: 700, color: warnings.length > 0 ? '#FF9500' : 'var(--text-secondary)' }}>{warnings.length}</div>
                 <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Warnings</div>
               </div>
            </div>
          </div>

          <div className="edi-split edi-split--validation">
            
            {/* Left Pane - Parsed Structure */}
            <div className="dash-card edi-panel">
              <div className="edi-panel__header">
                <h3 style={{ fontSize: '1rem', fontWeight: 600, margin: 0 }}>Structure Overview</h3>
                <div style={{ display: 'flex', gap: '12px', fontSize: '0.75rem' }}>
                  <span style={{ color: '#34C759', display: 'flex', alignItems: 'center', gap: '4px' }}><CheckCircle2 size={12} /> Valid</span>
                  <span style={{ color: '#FF3B30', display: 'flex', alignItems: 'center', gap: '4px' }}><AlertCircle size={12} /> Error</span>
                </div>
              </div>

              <div className="edi-panel__body custom-scrollbar">
                <div style={{ fontSize: '0.875rem' }}>
                  {activeSession.parsedJson?.segments?.map((seg: any, idx: number) => {
                     const segmentErrors = activeSession.errors?.filter(e => e.segment === seg.segmentId || e.segment.includes(seg.segmentId)) || [];
                     const hasError = segmentErrors.length > 0;
                     const nodeKey = `seg_val_${idx}`;

                     return (
                       <div key={idx} style={{ padding: '8px 0' }}>
                         <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: hasError ? 'pointer' : 'default', background: hasError ? 'rgba(255, 59, 48, 0.05)' : 'transparent', padding: '6px 8px', borderRadius: '4px' }} onClick={(e) => hasError && toggleNode(nodeKey, e)}>
                           <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                             {hasError ? (expandedNodes[nodeKey] ? <ChevronDown size={16} color="#FF3B30" /> : <ChevronRight size={16} color="#FF3B30" />) : <ChevronRight size={16} color="var(--text-secondary)" />}
                             <span style={{ color: hasError ? '#FF3B30' : 'var(--text-secondary)', fontWeight: 600 }}>{seg.segmentId}</span>
                           </div>
                           {hasError && <span style={{ fontSize: '0.75rem', background: '#FF3B30', color: '#fff', padding: '2px 6px', borderRadius: '4px' }}>{segmentErrors.length} errors</span>}
                         </div>
                         
                         {hasError && expandedNodes[nodeKey] && (
                           <div style={{ paddingLeft: '24px', marginTop: '8px' }}>
                             {segmentErrors.map((err, eIdx) => (
                               <div key={eIdx} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '4px 8px', background: 'rgba(255, 59, 48, 0.1)', color: '#fff', borderLeft: '2px solid #FF3B30', marginBottom: '4px' }}>
                                 <AlertCircle size={12} color="#FF3B30" /> <span style={{ fontWeight: 600, color: '#FF3B30' }}>{err.id || 'ERR'}</span> <span style={{ fontSize: '0.75rem' }}>{err.description}</span>
                               </div>
                             ))}
                           </div>
                         )}
                       </div>
                     );
                  })}
                </div>
              </div>
            </div>

            {/* Right Pane - Error List */}
            <div className="dash-card edi-panel">
              <div className="edi-panel__header">
                <div className="edi-filter-bar">
                  <button
                    style={{ background: activeFilter === 'all' ? '#0050FF' : 'transparent', color: activeFilter === 'all' ? '#fff' : 'var(--text-secondary)', border: activeFilter === 'all' ? 'none' : '1px solid rgba(255,255,255,0.15)', padding: '6px 16px', borderRadius: '24px', fontSize: '0.875rem' }}
                    onClick={() => setActiveFilter('all')}
                  >
                    All <span style={{ marginLeft: '4px', background: activeFilter === 'all' ? 'rgba(255,255,255,0.2)' : 'rgba(255,255,255,0.08)', padding: '2px 6px', borderRadius: '12px' }}>{activeSession.errors?.length || 0}</span>
                  </button>
                  <button
                    style={{ background: activeFilter === 'errors' ? 'rgba(255, 59, 48, 0.12)' : 'transparent', color: '#FF3B30', border: '1px solid rgba(255, 59, 48, 0.2)', padding: '6px 16px', borderRadius: '24px', fontSize: '0.875rem' }}
                    onClick={() => setActiveFilter('errors')}
                  >
                    Errors <span style={{ marginLeft: '4px', background: activeFilter === 'errors' ? 'rgba(255, 59, 48, 0.25)' : 'rgba(255, 59, 48, 0.15)', padding: '2px 6px', borderRadius: '12px' }}>{errors.length}</span>
                  </button>
                  <button
                    style={{ background: activeFilter === 'warnings' ? 'rgba(255, 149, 0, 0.12)' : 'transparent', color: '#FF9500', border: '1px solid rgba(255, 149, 0, 0.2)', padding: '6px 16px', borderRadius: '24px', fontSize: '0.875rem' }}
                    onClick={() => setActiveFilter('warnings')}
                  >
                    Warnings <span style={{ marginLeft: '4px', background: activeFilter === 'warnings' ? 'rgba(255, 149, 0, 0.25)' : 'rgba(255, 149, 0, 0.15)', padding: '2px 6px', borderRadius: '12px' }}>{warnings.length}</span>
                  </button>
                </div>
              </div>

              <div className="edi-panel__body custom-scrollbar">
                
                {filteredIssues.length === 0 ? (
                   <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-secondary)' }}>
                      <CheckCircle2 size={48} color="#34C759" style={{ marginBottom: '16px', opacity: 0.5 }} />
                      <h3>Clean File</h3>
                      <p>No validation errors detected!</p>
                   </div>
                ) : (
                  filteredIssues.map((err, i) => (
                    <div key={i} style={{ background: err.severity === 'Warning' ? 'rgba(255, 149, 0, 0.05)' : 'rgba(255, 59, 48, 0.05)', border: `1px solid ${err.severity === 'Warning' ? 'rgba(255, 149, 0, 0.2)' : 'rgba(255, 59, 48, 0.2)'}`, borderRadius: '8px', padding: '16px', marginBottom: '16px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            {err.severity === 'Warning' ? <AlertTriangle size={16} color="#FF9500" /> : <AlertCircle size={16} color="#FF3B30" />}
                            <span style={{ color: '#00D6FF', fontWeight: 600, fontSize: '0.875rem' }}>{err.id || `ERR-${i+1}`}</span>
                            <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Segment: {err.segment}</span>
                        </div>
                      </div>
                      <div style={{ fontWeight: 600, marginBottom: '16px' }}>{err.description}</div>
                      
                      {/* AI Suggestion Logic from backend Fix objects if mapped */}
                      {activeSession.fixes?.find(f => f.errorId === err.id) && (
                        <div style={{ background: 'rgba(0, 80, 255, 0.1)', border: '1px solid rgba(0, 80, 255, 0.2)', padding: '12px', borderRadius: '8px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#80EEFF', marginBottom: '4px', fontSize: '0.75rem', fontWeight: 600 }}>
                            <Wrench size={12} /> AI Suggestion Available
                          </div>
                          <div style={{ fontSize: '0.875rem' }}>{activeSession.fixes.find(f => f.errorId === err.id)?.description}</div>
                        </div>
                      )}
                    </div>
                  ))
                )}

              </div>
            </div>

          </div>
        </>
      )}
    </div>
  );
}
