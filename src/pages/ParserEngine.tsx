import React, { useEffect, useRef, useState } from 'react';
import { Play, Search, Filter, ChevronDown, ChevronRight, Copy, FileText } from 'lucide-react';
import { useSession } from '../context/SessionContext';
import { api } from '../services/api';

export default function ParserEngine() {
  const { activeSession, isLoading } = useSession();
  const [expandedNodes, setExpandedNodes] = useState<Record<string, boolean>>({});
  const [selectedSegmentIdx, setSelectedSegmentIdx] = useState<number | null>(null);

  const [segmentExplanation, setSegmentExplanation] = useState<string>('');
  const [segmentExplanationLoading, setSegmentExplanationLoading] = useState<boolean>(false);
  const [segmentExplanationError, setSegmentExplanationError] = useState<string>('');
  const explainReqIdRef = useRef(0);

  const toggleNode = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setExpandedNodes(prev => ({ ...prev, [id]: !prev[id] }));
  };

  if (!activeSession) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-secondary)' }}>
         <FileText size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
         <h3>No Active Session</h3>
         <p>Please upload a file to view its parsed structure.</p>
      </div>
    );
  }

  const segments = activeSession.parsedJson?.segments || [];
  const selectedSegment = selectedSegmentIdx !== null ? segments[selectedSegmentIdx] : null;

  useEffect(() => {
    const seg = selectedSegment;
    if (!seg || !seg.segmentId) {
      setSegmentExplanation('');
      setSegmentExplanationError('');
      setSegmentExplanationLoading(false);
      return;
    }

    const requestId = ++explainReqIdRef.current;
    setSegmentExplanationLoading(true);
    setSegmentExplanationError('');
    setSegmentExplanation('');

    (async () => {
      try {
        const explanation = await api.explainSegment(seg.segmentId, seg.raw);
        if (explainReqIdRef.current !== requestId) return;
        setSegmentExplanation(explanation);
      } catch (e: any) {
        if (explainReqIdRef.current !== requestId) return;
        setSegmentExplanationError(e?.message || 'Failed to load explanation');
      } finally {
        if (explainReqIdRef.current !== requestId) return;
        setSegmentExplanationLoading(false);
      }
    })();
  }, [selectedSegmentIdx]);

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '8px' }}>Parser Engine</h1>
          <p style={{ color: 'var(--text-secondary)' }}>Interactive EDI file structure viewer with segment-level details</p>
        </div>
        <div style={{ display: 'flex', gap: '16px' }}>
          <button className="btn primary" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Play size={16} /> Parse File
          </button>
          
          <div style={{ display: 'flex', alignItems: 'center', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', padding: '8px 16px', borderRadius: '8px' }}>
            <Search size={16} color="var(--text-secondary)" style={{ marginRight: '8px' }} />
            <input type="text" placeholder="Search segments..." style={{ background: 'transparent', border: 'none', color: '#fff', outline: 'none', width: '150px', fontSize: '0.875rem' }} />
          </div>

          <button className="btn outline" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Filter size={16} /> Filters
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '24px', flex: 1, minHeight: 0 }}>
        
        {/* Left Pane - EDI Structure */}
        <div className="dash-card" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', paddingBottom: '16px', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
             <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
               <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>EDI Structure</h3>
               <span style={{ fontSize: '0.75rem', background: 'rgba(255,255,255,0.1)', padding: '2px 8px', borderRadius: '12px' }}>{activeSession.filename}</span>
             </div>
          </div>
          
          <div style={{ flex: 1, overflowY: 'auto', paddingRight: '8px' }} className="custom-scrollbar">
            {isLoading ? <div style={{ color: 'var(--text-secondary)', padding: '20px' }}>Loading document structure...</div> : (
              <div style={{ fontSize: '0.875rem' }}>
                
                {segments.map((seg: any, idx: number) => {
                   const isSelected = selectedSegmentIdx === idx;
                   const nodeKey = `seg_${idx}`;

                   return (
                     <div key={idx} style={{ padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.02)' }}>
                        <div 
                           style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer', background: isSelected ? 'rgba(0, 80, 255, 0.1)' : 'transparent', padding: '4px 8px', borderRadius: '4px', borderLeft: isSelected ? '2px solid #0050FF' : '2px solid transparent' }} 
                           onClick={() => setSelectedSegmentIdx(idx)}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }} onClick={(e) => toggleNode(nodeKey, e)}>
                            {expandedNodes[nodeKey] ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                            <span style={{ color: '#00D6FF', fontWeight: 600 }}>{seg.segmentId}</span>
                            <span style={{ color: 'var(--text-secondary)' }}>Segment</span>
                          </div>
                        </div>

                        {expandedNodes[nodeKey] && (
                          <div style={{ paddingLeft: '24px', marginTop: '8px' }}>
                            {seg.elements?.map((el: any, eIdx: number) => (
                               <div key={eIdx} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', color: 'var(--text-secondary)' }}>
                                 <span>{el.id}</span>
                                 <span style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                                   <span style={{ color: '#fff' }}>{el.value}</span>
                                 </span>
                               </div>
                            ))}
                          </div>
                        )}
                     </div>
                   );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right Pane - Detail View */}
        <div className="dash-card" style={{ display: 'flex', flexDirection: 'column', padding: '32px' }}>
          
          {!selectedSegment ? (
             <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-secondary)' }}>
                Select a segment from the tree to view details.
             </div>
          ) : (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span style={{ background: '#0050FF', padding: '4px 8px', borderRadius: '4px', fontSize: '0.875rem', fontWeight: 600 }}>{selectedSegment.segmentId}</span>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: 600 }}>Segment Details</h2>
                </div>
                <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Index {selectedSegmentIdx}</span>
              </div>
              
              <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '24px' }}>
                Raw Data View
              </div>

              <div style={{ marginBottom: '32px' }}>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>Raw EDI String</div>
                <div style={{ display: 'flex', alignItems: 'center', background: 'rgba(0,0,0,0.3)', padding: '12px 16px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
                  <span style={{ flex: 1, fontFamily: 'monospace', fontSize: '1rem', wordBreak: 'break-all' }}>{selectedSegment.raw}</span>
                  <Copy size={16} color="var(--text-secondary)" style={{ cursor: 'pointer' }} />
                </div>
              </div>

              <div style={{ marginBottom: '32px' }}>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>Natural Language Explanation</div>
                <div style={{ background: 'rgba(255,255,255,0.02)', padding: '12px 16px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)', minHeight: '64px' }}>
                  {segmentExplanationLoading ? (
                    <div style={{ color: 'var(--text-secondary)' }}>Explaining segment...</div>
                  ) : segmentExplanationError ? (
                    <div style={{ color: '#FF3B30' }}>{segmentExplanationError}</div>
                  ) : segmentExplanation ? (
                    <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>{segmentExplanation}</div>
                  ) : (
                    <div style={{ color: 'var(--text-secondary)' }}>Select a segment to see its explanation.</div>
                  )}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>Elements</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  
                  {selectedSegment.elements?.map((el: any, i: number) => (
                    <div key={i} style={{ background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '8px' }}>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>{el.id}</div>
                      <div style={{ fontWeight: 600, wordBreak: 'break-all' }}>{el.value || '(empty)'}</div>
                    </div>
                  ))}

                </div>
              </div>
            </>
          )}

        </div>

      </div>
    </div>
  );
}
