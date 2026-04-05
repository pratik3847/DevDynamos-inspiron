import { MouseEvent, useMemo, useState } from 'react';
import { Play, CheckCircle2, AlertTriangle, AlertCircle, ChevronDown, ChevronRight, FileCode, Wrench, FileText } from 'lucide-react';
import { useSession } from '../context/SessionContext';

export default function ValidationEngine() {
  const { activeSession, isLoading, refreshSession } = useSession();
  const [expandedNodes, setExpandedNodes] = useState<Record<string, boolean>>({});
  const [activeFilter, setActiveFilter] = useState<'all' | 'errors' | 'warnings'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showFixableOnly, setShowFixableOnly] = useState(false);

  const toggleNode = (id: string, e: MouseEvent<HTMLDivElement>) => {
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
  const segmentsWithIssues = new Set(uploadedIssues.map(e => e.segment));
  const validSegments = totalSegments - segmentsWithIssues.size;
  const healthScore = totalSegments > 0 ? Math.round((validSegments / totalSegments) * 100) : 100;

  const fixesByErrorId = useMemo(() => {
    const map = new Map<string, any>();
    (activeSession.fixes || []).forEach((f) => {
      if (!f?.errorId) return;
      map.set(String(f.errorId), f);
    });
    return map;
  }, [activeSession.fixes]);

  const filteredIssues = useMemo(() => {
    const base = activeFilter === 'errors' ? errors : activeFilter === 'warnings' ? warnings : uploadedIssues;
    const query = searchQuery.trim().toLowerCase();
    return base.filter((err) => {
      if (showFixableOnly && !fixesByErrorId.get(String(err.id || ''))) return false;
      if (!query) return true;
      const haystack = [
        err.id,
        err.loop,
        err.segment,
        err.element,
        err.description,
        err.rule,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      return haystack.includes(query);
    });
  }, [activeFilter, errors, warnings, uploadedIssues, fixesByErrorId, searchQuery, showFixableOnly]);

  return (
    <div className="edi-page">
      <div className="edi-page__header">
        <div>
          <div className="ui-kicker">Validation Suite</div>
          <h1 className="page-title" style={{ marginBottom: '8px' }}>Validation Engine</h1>
          <p className="page-subtitle">Validate EDI files against HIPAA and custom rules</p>
        </div>
        <div className="edi-page__actions">
          <button className="btn outline" style={{ display: 'flex', alignItems: 'center', gap: '8px' }} onClick={refreshSession} disabled={isLoading}>
             <Play size={16} /> {isLoading ? 'Revalidating...' : 'Re-Validate'}
          </button>
        </div>
      </div>

      {isLoading ? (
         <div style={{ padding: '20px', color: 'var(--text-secondary)' }}>Loading Validation Metrics...</div>
      ) : (
        <>
          <div className="dash-card validation-summary" style={{ marginBottom: '24px' }}>
            <div className="validation-summary__head">
              <div className="validation-summary__title">
                <div className={`validation-summary__icon ${errors.length > 0 ? 'is-error' : 'is-ok'}`}>
                  {errors.length > 0 ? <AlertCircle size={22} color="#FF3B30" /> : <CheckCircle2 size={22} color="#34C759" />}
                </div>
                <div>
                  <div className="validation-summary__headline">Validation Complete</div>
                  <div className="validation-summary__file">{activeSession.filename}</div>
                </div>
              </div>
              <div className={`validation-summary__chip ${errors.length > 0 ? 'is-error' : 'is-ok'}`}>
                {errors.length > 0 ? 'Needs Attention' : 'Clean'}
              </div>
            </div>

            <div className="validation-health">
              <div className="validation-health__meta">
                <span>Validation Health</span>
                <span className={`validation-health__score ${healthScore < 100 ? 'is-error' : 'is-ok'}`}>{healthScore}%</span>
              </div>
              <div className="validation-health__bar">
                <div
                  className={`validation-health__fill ${healthScore < 100 ? 'is-error' : 'is-ok'}`}
                  style={{ width: `${healthScore}%` }}
                ></div>
              </div>
            </div>
          </div>

          <div className="edi-grid edi-grid--4" style={{ marginBottom: '24px' }}>
            <div className="dash-card validation-metric validation-metric--neutral">
              <div className="validation-metric__icon is-blue"><FileCode size={20} color="#0050FF" /></div>
              <div>
                <div className="validation-metric__value">{totalSegments}</div>
                <div className="validation-metric__label">Total Segments</div>
              </div>
            </div>
            <div className="dash-card validation-metric validation-metric--ok">
              <div className="validation-metric__icon is-green"><CheckCircle2 size={20} color="#34C759" /></div>
              <div>
                <div className="validation-metric__value">{validSegments}</div>
                <div className="validation-metric__label">Valid</div>
              </div>
            </div>
            <div className={`dash-card validation-metric validation-metric--error ${errors.length > 0 ? 'is-active' : ''}`}>
              <div className="validation-metric__icon is-red"><AlertCircle size={20} color="#FF3B30" /></div>
              <div>
                <div className="validation-metric__value is-red">{errors.length}</div>
                <div className="validation-metric__label">Errors</div>
              </div>
            </div>
            <div className={`dash-card validation-metric validation-metric--warn ${warnings.length > 0 ? 'is-active' : ''}`}>
              <div className="validation-metric__icon is-amber"><AlertTriangle size={20} color="#FF9500" /></div>
              <div>
                <div className="validation-metric__value is-amber">{warnings.length}</div>
                <div className="validation-metric__label">Warnings</div>
              </div>
            </div>
          </div>

          <div className="edi-split edi-split--validation">
            
            {/* Left Pane - Parsed Structure */}
            <div className="dash-card edi-panel">
              <div className="edi-panel__header">
                <h3 style={{ fontSize: '1rem', fontWeight: 600, margin: 0 }}>Structure Overview</h3>
              </div>

              <div className="edi-panel__body custom-scrollbar">
                <div className="validation-structure">
                  {activeSession.parsedJson?.segments?.map((seg: any, idx: number) => {
                     const segmentErrors = uploadedIssues.filter(e => e.segment === seg.segmentId || e.segment.includes(seg.segmentId));
                     const hasError = segmentErrors.length > 0;
                     const nodeKey = `seg_val_${idx}`;

                     return (
                       <div key={idx} className="validation-structure__item">
                         <div
                           className={`validation-structure__row ${hasError ? 'is-error' : ''}`}
                           onClick={(e) => hasError && toggleNode(nodeKey, e)}
                           role={hasError ? 'button' : undefined}
                         >
                           <div className="validation-structure__left">
                             {hasError ? (
                               expandedNodes[nodeKey] ? <ChevronDown size={14} color="#FF3B30" /> : <ChevronRight size={14} color="#FF3B30" />
                             ) : (
                               <ChevronRight size={14} color="var(--text-secondary)" />
                             )}
                             <span className={`validation-structure__label ${hasError ? 'is-error' : ''}`}>{seg.segmentId}</span>
                           </div>
                           {hasError && (
                             <span className="validation-structure__badge">{segmentErrors.length} errors</span>
                           )}
                         </div>
                         
                         {hasError && expandedNodes[nodeKey] && (
                           <div className="validation-structure__details">
                             {segmentErrors.map((err, eIdx) => (
                               <div key={eIdx} className="validation-structure__detail">
                                 <AlertCircle size={12} color="#FF3B30" />
                                 <span className="validation-structure__code">{err.id || 'ERR'}</span>
                                  {err.loop ? <span className="validation-structure__loop">Loop {err.loop}</span> : null}
                                 <span className="validation-structure__text">{err.description}</span>
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
                    className={`validation-filter__btn is-all ${activeFilter === 'all' ? 'is-active' : ''}`}
                    onClick={() => setActiveFilter('all')}
                  >
                    All <span className="validation-filter__count">{uploadedIssues.length}</span>
                  </button>
                  <button
                    className={`validation-filter__btn is-error ${activeFilter === 'errors' ? 'is-active' : ''}`}
                    onClick={() => setActiveFilter('errors')}
                  >
                    Errors <span className="validation-filter__count">{errors.length}</span>
                  </button>
                  <button
                    className={`validation-filter__btn is-warning ${activeFilter === 'warnings' ? 'is-active' : ''}`}
                    onClick={() => setActiveFilter('warnings')}
                  >
                    Warnings <span className="validation-filter__count">{warnings.length}</span>
                  </button>
                  <input
                    className="edi-search"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search segments, loops, IDs"
                  />
                  <button
                    className={`toggle-pill ${showFixableOnly ? 'is-active' : ''}`}
                    onClick={() => setShowFixableOnly((prev) => !prev)}
                    type="button"
                  >
                    Has Fix
                  </button>
                </div>
              </div>

              <div className="edi-panel__body custom-scrollbar">
                
                {filteredIssues.length === 0 ? (
                   <div className="validation-empty">
                      <CheckCircle2 size={48} color="#34C759" style={{ marginBottom: '16px', opacity: 0.5 }} />
                      <h3>Clean File</h3>
                      <p>No validation errors detected!</p>
                   </div>
                ) : (
                  filteredIssues.map((err, i) => {
                    const tone = err.severity === 'Warning' ? 'is-warning' : 'is-error';
                    const fix = fixesByErrorId.get(String(err.id || ''));
                    return (
                      <div key={i} className={`validation-issue ${tone}`}>
                        <div className="validation-issue__header">
                          <div className="validation-issue__meta">
                              {err.severity === 'Warning' ? <AlertTriangle size={16} color="#FF9500" /> : <AlertCircle size={16} color="#FF3B30" />}
                              <span className="validation-issue__id">{err.id || `ERR-${i + 1}`}</span>
                              <span className="validation-issue__segment">Segment: {err.segment}</span>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            {fix ? (
                              <span className="status-badge review">Fix Available</span>
                            ) : (
                              <span className="status-badge manual">Manual</span>
                            )}
                            <span className={`validation-issue__badge ${tone}`}>{err.severity}</span>
                          </div>
                        </div>
                        <div className="validation-issue__desc">{err.description}</div>
                        
                        {/* AI Suggestion Logic from backend Fix objects if mapped */}
                        {fix && (
                          <div className="validation-issue__suggestion">
                            <div className="validation-issue__suggestion-title">
                              <Wrench size={12} /> AI Suggestion Available
                            </div>
                            <div className="validation-issue__suggestion-text">{fix.description}</div>
                          </div>
                        )}
                      </div>
                    );
                  })
                )}

              </div>
            </div>

          </div>
        </>
      )}
    </div>
  );
}
