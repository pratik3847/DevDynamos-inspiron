import React, { useEffect, useRef, useState } from 'react';
import { Play, Search, Filter, ChevronDown, ChevronRight, Copy, FileText } from 'lucide-react';
import { useSession } from '../context/SessionContext';
import { api } from '../services/api';

const SEGMENT_ELEMENT_LABELS: Record<string, Record<number, string>> = {
  ISA: {
    1: 'Authorization Information Qualifier',
    2: 'Authorization Information',
    3: 'Security Information Qualifier',
    4: 'Security Information',
    5: 'Interchange Sender Qualifier',
    6: 'Interchange Sender ID',
    7: 'Interchange Receiver Qualifier',
    8: 'Interchange Receiver ID',
    9: 'Interchange Date',
    10: 'Interchange Time',
    11: 'Interchange Control Standards Identifier',
    12: 'Interchange Control Version Number',
    13: 'Interchange Control Number',
    14: 'Acknowledgment Requested',
    15: 'Usage Indicator',
    16: 'Component Element Separator',
  },
  GS: {
    1: 'Functional Identifier Code',
    2: "Application Sender's Code",
    3: "Application Receiver's Code",
    4: 'Date',
    5: 'Time',
    6: 'Group Control Number',
    7: 'Responsible Agency Code',
    8: 'Version / Release / Industry Identifier Code',
  },
  ST: {
    1: 'Transaction Set Identifier Code',
    2: 'Transaction Set Control Number',
  },
  BHT: {
    1: 'Hierarchical Structure Code',
    2: 'Transaction Set Purpose Code',
    3: 'Reference Identification',
    4: 'Date',
    5: 'Time',
  },
  HL: {
    1: 'Hierarchical ID Number',
    2: 'Hierarchical Parent ID Number',
    3: 'Hierarchical Level Code',
    4: 'Hierarchical Child Code',
  },
  SBR: {
    1: 'Payer Responsibility Sequence Number Code',
    2: 'Individual Relationship Code',
    3: 'Reference Identification',
    4: 'Name',
    5: 'Insurance Type Code',
    6: 'Claim Filing Indicator Code',
    7: 'Coordination of Benefits Code',
    8: 'Yes/No Condition or Response Code',
  },
  NM1: {
    1: 'Entity Identifier Code',
    2: 'Entity Type Qualifier',
    3: 'Name Last or Organization Name',
    4: 'Name First',
    5: 'Name Middle',
    6: 'Name Prefix',
    7: 'Name Suffix',
    8: 'Identification Code Qualifier',
    9: 'Identification Code',
  },
  N3: {
    1: 'Address Information',
    2: 'Address Information 2',
  },
  N4: {
    1: 'City Name',
    2: 'State or Province Code',
    3: 'Postal Code',
    4: 'Country Code',
  },
  PER: {
    1: 'Contact Function Code',
    2: 'Name',
    3: 'Communication Number Qualifier 1',
    4: 'Communication Number 1',
    5: 'Communication Number Qualifier 2',
    6: 'Communication Number 2',
    7: 'Communication Number Qualifier 3',
    8: 'Communication Number 3',
  },
  REF: {
    1: 'Reference Identification Qualifier',
    2: 'Reference Identification',
  },
  DTP: {
    1: 'Date/Time Qualifier',
    2: 'Date Time Period Format Qualifier',
    3: 'Date Time Period',
  },
  CLM: {
    1: 'Patient Control Number',
    2: 'Total Claim Charge Amount',
    3: 'Claim Filing Indicator Code',
    4: 'Non-Institutional Claim Type Code',
    5: 'Health Care Service Location Information',
    6: 'Provider or Supplier Signature Indicator',
    7: 'Medicare Assignment Code',
    8: 'Benefits Assignment Certification Indicator',
    9: 'Release of Information Code',
    10: 'Patient Signature Source Code',
  },
  LX: {
    1: 'Assigned Number',
  },
  SV1: {
    1: 'Composite Medical Procedure Identifier',
    2: 'Line Item Charge Amount',
    3: 'Unit or Basis for Measurement Code',
    4: 'Service Unit Count',
    5: 'Place of Service Code',
    6: 'Diagnosis Code Pointer',
    7: 'Emergency Service Code',
    8: 'EPSDT Indicator',
    9: 'Family Planning Indicator',
    10: 'Copay Status Code',
  },
  SV2: {
    1: 'Service Line Revenue Code',
    2: 'Composite Medical Procedure Identifier',
    3: 'Line Item Charge Amount',
    4: 'Unit or Basis for Measurement Code',
    5: 'Service Unit Count',
  },
  HI: {
    1: 'Health Care Code Information',
  },
  GE: {
    1: 'Number of Transaction Sets Included',
    2: 'Group Control Number',
  },
  SE: {
    1: 'Number of Included Segments',
    2: 'Transaction Set Control Number',
  },
  IEA: {
    1: 'Number of Included Functional Groups',
    2: 'Interchange Control Number',
  },
};

const SEGMENT_DEPTH_ORDER: Record<string, number> = {
  ISA: 0,
  IEA: 0,
  GS: 1,
  GE: 1,
  ST: 2,
  SE: 2,
  BHT: 3,
  HL: 4,
  CLM: 5,
  SBR: 5,
  NM1: 6,
  N3: 6,
  N4: 6,
  PER: 6,
  REF: 6,
  DTP: 6,
  PRV: 6,
  HI: 6,
  LX: 6,
  SV1: 7,
  SV2: 7,
};

const getDashboardTheme = () => {
  if (typeof window === 'undefined') {
    return 'dark';
  }
  return localStorage.getItem('dashboard_theme') === 'light' ? 'light' : 'dark';
};

const isLightTheme = () => getDashboardTheme() === 'light';

const getElementLabel = (segmentId: string, elementId: string, position: number) => {
  const labels = SEGMENT_ELEMENT_LABELS[segmentId.toUpperCase()] || {};
  return labels[position] || elementId || `Element ${position.toString().padStart(2, '0')}`;
};

const getSegmentDepth = (segmentId: string) => {
  const upperSegmentId = segmentId.toUpperCase();
  return SEGMENT_DEPTH_ORDER[upperSegmentId] ?? 6;
};

export default function ParserEngine() {
  const { activeSession, isLoading } = useSession();
  const [expandedNodes, setExpandedNodes] = useState<Record<string, boolean>>({});
  const [selectedSegmentIdx, setSelectedSegmentIdx] = useState<number | null>(null);
  const [hoveredElementId, setHoveredElementId] = useState<string | null>(null);

  const [segmentExplanation, setSegmentExplanation] = useState<string>('');
  const [segmentExplanationLoading, setSegmentExplanationLoading] = useState<boolean>(false);
  const [segmentExplanationError, setSegmentExplanationError] = useState<string>('');
  const explainReqIdRef = useRef(0);

  const segments = activeSession?.parsedJson?.segments || [];
  const selectedSegment = selectedSegmentIdx !== null ? segments[selectedSegmentIdx] : null;

  const toggleNode = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setExpandedNodes(prev => ({ ...prev, [id]: !prev[id] }));
  };

  // Color palette for depth-based hierarchy coloring (works in both light and dark modes)
  const getDepthColor = (depth: number) => {
    const darkModeColors = [
      '#00D6FF',    // depth 0 - bright cyan
      '#03a9ce',    // depth 1 - medium cyan
      '#0e8fb0',    // depth 2 - dark cyan
      '#076989',    // depth 3 - darker cyan
    ];
    const lightModeColors = [
      '#0671db',    // depth 0 - bright blue
      '#004499',    // depth 1 - medium blue
      '#003366',    // depth 2 - dark blue
      '#023b73',    // depth 3 - darker blue
    ];
    const colors = isLightTheme() ? lightModeColors : darkModeColors;
    return colors[Math.min(depth, colors.length - 1)];
  };

  // Get text color based on theme
  const getTextColor = () => {
    return isLightTheme() ? 'var(--text-primary)' : 'var(--text-primary)';
  };

  const getSurfaceColor = (depth: number, isSelected: boolean, isHovered: boolean) => {
    const depthColor = getDepthColor(depth);
    if (isSelected) {
      return isLightTheme() ? `${depthColor}38` : `${depthColor}2E`;
    }
    if (isHovered) {
      return isLightTheme() ? `${depthColor}2E` : `${depthColor}24`;
    }
    return isLightTheme() ? `${depthColor}24` : `${depthColor}18`;
  };

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

  // Parse raw EDI and highlight hovered element
  const renderHighlightedRawEdi = (rawEdi: string, hoveredId: string | null) => {
    const rawTextStyle: React.CSSProperties = {
      display: 'block',
      width: '100%',
      fontFamily: 'monospace',
      fontSize: '1rem',
      whiteSpace: 'pre-wrap',
      overflowWrap: 'anywhere',
      wordBreak: 'break-word',
    };

    if (!hoveredId) {
      return <span style={rawTextStyle}>{rawEdi}</span>;
    }

    // Extract element index from ID (e.g., "NM101" -> element 0, "NM102" -> element 1)
    const selectedSegment = segments[selectedSegmentIdx!];
    const elementIndex = selectedSegment.elements?.findIndex((el: any) => el.id === hoveredId);
    
    if (elementIndex === undefined || elementIndex === -1) {
      return <span style={rawTextStyle}>{rawEdi}</span>;
    }

    // Split by * to get parts
    const parts = rawEdi.split('*');
    
    return (
      <span style={rawTextStyle}>
        {parts.map((part, idx) => (
          <React.Fragment key={idx}>
            {idx === elementIndex + 1 ? (
              <span style={{ background: '#3c92e8', color: '#000', fontWeight: 'bold', padding: '2px 4px', borderRadius: '2px' }}>
                {part}
              </span>
            ) : (
              part
            )}
            {idx < parts.length - 1 && '*'}
          </React.Fragment>
        ))}
      </span>
    );
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
                   const segmentDepth = getSegmentDepth(seg.segmentId || '');
                   const segmentColor = getDepthColor(segmentDepth);
                   const textColor = getTextColor();
                   const segmentSurface = getSurfaceColor(segmentDepth, isSelected, false);
                   const childSurface = isLightTheme() ? `${segmentColor}20` : `${segmentColor}14`;

                   return (
                     <div key={idx} style={{ marginBottom: '14px', marginLeft: `${segmentDepth * 14}px` }}>
                        <div 
                          style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer', background: segmentSurface, padding: '10px 14px', borderRadius: '10px', border: `1px solid ${segmentColor}55`, boxShadow: isSelected ? `0 0 0 1px ${segmentColor}33` : 'none', transition: 'all 0.2s ease' }} 
                           onClick={() => setSelectedSegmentIdx(idx)}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1 }} onClick={(e) => toggleNode(nodeKey, e)}>
                            {expandedNodes[nodeKey] ? <ChevronDown size={16} style={{ color: segmentColor }} /> : <ChevronRight size={16} style={{ color: segmentColor }} />}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                              <span style={{ color: segmentColor, fontWeight: 800, fontSize: '0.96rem', letterSpacing: '0.01em' }}>{seg.segmentId}</span>
                              <span style={{ color: 'var(--text-secondary)', fontSize: '0.76rem' }}>Level {segmentDepth}</span>
                            </div>
                          </div>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedSegmentIdx(idx);
                            }}
                            style={{
                              border: `1px solid ${segmentColor}88`,
                              background: isSelected ? `${segmentColor}44` : `${segmentColor}26`,
                              color: isLightTheme() ? '#0b2a52' : '#eaf8ff',
                              borderRadius: '999px',
                              fontSize: '0.72rem',
                              fontWeight: 700,
                              padding: '4px 10px',
                              cursor: 'pointer',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            Details
                          </button>
                        </div>

                        {expandedNodes[nodeKey] && (
                          <div style={{ marginTop: '8px', marginLeft: '16px', padding: '12px', borderRadius: '10px', background: childSurface, border: `1px solid ${segmentColor}33` }}>
                            {seg.elements?.map((el: any, eIdx: number) => {
                               const elementDepth = segmentDepth + 1;
                               const elementColor = getDepthColor(elementDepth);
                               const isHovered = hoveredElementId === el.id;
                               const elementPosition = Number(el.position || String(el.id || '').replace(/\D+/g, '')) || eIdx + 1;
                               const elementLabel = getElementLabel(seg.segmentId || '', el.id || '', elementPosition);
                               return (
                                 <div 
                                   key={eIdx} 
                                   style={{ 
                                     display: 'flex', 
                                     flexDirection: 'column',
                                     gap: '6px',
                                     padding: '10px 12px', 
                                     borderRadius: '8px',
                                     background: isHovered ? `${elementColor}30` : (isLightTheme() ? `${elementColor}24` : `${elementColor}18`),
                                     cursor: 'pointer',
                                     transition: 'all 0.15s ease',
                                     border: `1px solid ${isHovered ? '#d323aa' : `${elementColor}55`}`,
                                     marginBottom: '2px'
                                   }}
                                   onMouseEnter={() => setHoveredElementId(el.id)}
                                   onMouseLeave={() => setHoveredElementId(null)}
                                 >
                                   <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
                                     <span style={{ color: isHovered ? '#c61254' : elementColor, fontSize: '0.78rem', fontWeight: 800, minWidth: '54px' }}>{el.id}</span>
                                     <span style={{ color: 'var(--text-secondary)', fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Element</span>
                                   </div>
                                   <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                     <span style={{ color: isHovered ? '#a703a4' : textColor, fontWeight: 700, fontSize: '0.82rem', wordBreak: 'break-word' }}>{elementLabel}</span>
                                     <span style={{ color: isHovered ? '#7826f3' : 'var(--text-secondary)', fontSize: '0.8rem', wordBreak: 'break-all' }}>{el.value || '(empty)'}</span>
                                   </div>
                                 </div>
                               );
                            })}
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
                  <span style={{ background: '#086acc', padding: '4px 8px', borderRadius: '4px', fontSize: '0.875rem', fontWeight: 600 }}>{selectedSegment.segmentId}</span>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: 600 }}>Segment Details</h2>
                </div>
                <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Index {selectedSegmentIdx}</span>
              </div>
              
              <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '24px' }}>
                Raw Data View
              </div>

              <div style={{ marginBottom: '32px' }}>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>Raw EDI String</div>
                <div style={{ display: 'flex', alignItems: 'flex-start', background: 'rgba(0,0,0,0.3)', padding: '12px 16px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', overflow: 'hidden' }}>
                  <span style={{ flex: 1, minWidth: 0, maxWidth: '100%' }}>
                    {renderHighlightedRawEdi(selectedSegment.raw, hoveredElementId)}
                  </span>
                  <Copy size={16} color="var(--text-secondary)" style={{ cursor: 'pointer' }} />
                </div>
              </div>

              <div style={{ marginBottom: '32px' }}>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>Natural Language Explanation</div>
                <div style={{ background: 'rgba(222, 15, 15, 0.02)', padding: '12px 16px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)', minHeight: '64px' }}>
                  {segmentExplanationLoading ? (
                    <div style={{ color: 'var(--text-secondary)' }}>Explaining segment...</div>
                  ) : segmentExplanationError ? (
                    <div style={{ color: '#32050299' }}>{segmentExplanationError}</div>
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
                    <div key={i} style={{ background: 'rgba(255, 255, 255, 0)', padding: '12px', borderRadius: '8px' }}>
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
