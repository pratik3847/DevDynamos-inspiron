import React, { useMemo, useState } from 'react';
import { AlertTriangle, ChevronDown, ChevronRight, Filter } from 'lucide-react';
import { useSession } from '../context/SessionContext';

interface ClaimRecord {
  key: string;
  claimId: string;
  patientName: string;
  billedAmount: number;
  paidAmount: number;
  patientResponsibility: number;
  statusCode: string;
  statusLabel: string;
  statusMeta: StatusMeta;
  adjustments: AdjustmentRecord[];
  hasAdjustments: boolean;
}

interface AdjustmentRecord {
  groupCode: string;
  reasonCode: string;
  amount: number;
  explanation?: string;
}

type StatusMeta = {
  label: string;
  color: string;
  bg: string;
  border: string;
};

const STATUS_MAP: Record<string, StatusMeta> = {
  '1': {
    label: 'Processed as Billed',
    color: '#1E8E3E',
    bg: 'rgba(30, 142, 62, 0.14)',
    border: 'rgba(30, 142, 62, 0.35)',
  },
  '2': {
    label: 'Processed with Adjustments',
    color: '#B36B00',
    bg: 'rgba(179, 107, 0, 0.14)',
    border: 'rgba(179, 107, 0, 0.35)',
  },
  '3': {
    label: 'Denied',
    color: '#C5221F',
    bg: 'rgba(197, 34, 31, 0.14)',
    border: 'rgba(197, 34, 31, 0.35)',
  },
  '4': {
    label: 'Secondary Payer',
    color: '#5F6368',
    bg: 'rgba(95, 99, 104, 0.16)',
    border: 'rgba(95, 99, 104, 0.35)',
  },
};

const DEFAULT_STATUS: StatusMeta = {
  label: 'Unknown Status',
  color: 'var(--text-secondary)',
  bg: 'rgba(127, 127, 127, 0.12)',
  border: 'rgba(127, 127, 127, 0.3)',
};

function parseClaimsFromSession(parsedJson: any): ClaimRecord[] {
  // Try to get claims from different possible structures
  // Priority: parsed_835 (specialized parser) > parsedJson.claims > parsed_data.claims
  const claims = parsedJson?.parsed_835?.claims || 
                  parsedJson?.claims || 
                  parsedJson?.parsed_data?.claims || 
                  [];
  
  if (!Array.isArray(claims)) return [];

  return claims.map((claim: any, index: number) => {
    const statusCode = String(claim.claim_status_code || claim.statusCode || '');
    const statusMeta = STATUS_MAP[statusCode] || DEFAULT_STATUS;
    
    const adjustments = (claim.adjustments || []).map((adj: any) => ({
      groupCode: adj.group_code || adj.groupCode || '',
      reasonCode: adj.reason_code || adj.reasonCode || '',
      amount: parseFloat(adj.adjustment_amount || adj.amount || 0),
      explanation: adj.explanation || ''
    }));

    return {
      key: `claim_${index}_${claim.claim_submitter_identifier || claim.claim_control_number || claim.claimId || index}`,
      claimId: claim.claim_submitter_identifier || claim.claim_control_number || claim.claimId || `CLM${index}`,
      patientName: claim.patient_name || claim.patientName || 'Unknown Patient',
      billedAmount: parseFloat(claim.total_claim_charge_amount || claim.total_billed_amount || claim.billedAmount || 0),
      paidAmount: parseFloat(claim.claim_payment_amount || claim.total_paid_amount || claim.paidAmount || 0),
      patientResponsibility: parseFloat(claim.patient_responsibility_amount || claim.patientResponsibility || 0),
      statusCode,
      statusLabel: statusMeta.label,
      statusMeta,
      adjustments,
      hasAdjustments: adjustments.length > 0,
    };
  });
}

export default function Dashboard835() {
  const { activeSession, isLoading } = useSession();
  const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});
  const [showAdjustedOnly, setShowAdjustedOnly] = useState(false);

  const claims = useMemo(() => {
    if (!activeSession?.parsedJson) return [];
    
    const allClaims = parseClaimsFromSession(activeSession.parsedJson);
    
    if (!showAdjustedOnly) return allClaims;
    
    return allClaims.filter(claim => claim.hasAdjustments);
  }, [activeSession?.parsedJson, showAdjustedOnly]);

  const totalClaims = claims.length;
  const totalBilled = claims.reduce((sum, claim) => sum + claim.billedAmount, 0);
  const totalPaid = claims.reduce((sum, claim) => sum + claim.paidAmount, 0);
  const totalAdjustments = claims.filter(claim => claim.hasAdjustments).length;

  const toggleExpand = (key: string) => {
    setExpandedRows(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const explainAdjustment = async (reasonCode: string) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/parser/explain-adjustment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          carc_code: reasonCode,
          context: `Claim adjustment in remittance file ${activeSession?.filename}`
        })
      });

      if (response.ok) {
        const data = await response.json();
        alert(`CARC-${reasonCode}: ${data.explanation}`);
      }
    } catch (error) {
      console.error('Error explaining adjustment:', error);
    }
  };

  if (!activeSession) {
    return (
      <div className="dash-card" style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <h2 style={{ marginBottom: '8px' }}>835 Remittance Dashboard</h2>
        <p style={{ color: 'var(--text-secondary)' }}>
          Upload/select an 835 remittance file first to view payment analysis.
        </p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px', flexWrap: 'wrap' }}>
        <div>
          <h1 style={{ fontSize: '1.55rem', fontWeight: 700, marginBottom: '8px' }}>835 Remittance Dashboard</h1>
          <p style={{ color: 'var(--text-secondary)' }}>
            File: <strong>{activeSession.filename}</strong> - Payment remittance with claim-level details and AI explanations.
          </p>
        </div>

        <div className="dash-card" style={{ padding: '12px 14px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Filter size={16} color="var(--text-secondary)" />
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={showAdjustedOnly}
              onChange={(e) => setShowAdjustedOnly(e.target.checked)}
              style={{ accentColor: '#f59e0b' }}
            />
            <span style={{ fontSize: '0.88rem', fontWeight: 600 }}>Show Only Adjusted Claims</span>
          </label>
        </div>
      </div>

      {/* Statistics Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
        <div className="dash-card" style={{ padding: '16px' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Total Claims</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 700 }}>{isLoading ? '...' : totalClaims}</div>
        </div>
        <div className="dash-card" style={{ padding: '16px' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Total Billed</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 700 }}>{isLoading ? '...' : `$${totalBilled.toLocaleString()}`}</div>
        </div>
        <div className="dash-card" style={{ padding: '16px' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Total Paid</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 700, color: '#1E8E3E' }}>{isLoading ? '...' : `$${totalPaid.toLocaleString()}`}</div>
        </div>
        <div className="dash-card" style={{ padding: '16px' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Claims with Adjustments</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 700, color: '#f59e0b' }}>{isLoading ? '...' : totalAdjustments}</div>
        </div>
      </div>

      {/* Claims Table */}
      <div className="dash-card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '1000px' }}>
            <thead>
              <tr style={{ background: 'rgba(255,255,255,0.04)' }}>
                <th style={{ textAlign: 'left', padding: '14px 16px', fontSize: '0.78rem', letterSpacing: '0.03em', color: 'var(--text-secondary)' }}>Claim</th>
                <th style={{ textAlign: 'left', padding: '14px 16px', fontSize: '0.78rem', letterSpacing: '0.03em', color: 'var(--text-secondary)' }}>Patient</th>
                <th style={{ textAlign: 'left', padding: '14px 16px', fontSize: '0.78rem', letterSpacing: '0.03em', color: 'var(--text-secondary)' }}>Status</th>
                <th style={{ textAlign: 'right', padding: '14px 16px', fontSize: '0.78rem', letterSpacing: '0.03em', color: 'var(--text-secondary)' }}>Billed</th>
                <th style={{ textAlign: 'right', padding: '14px 16px', fontSize: '0.78rem', letterSpacing: '0.03em', color: 'var(--text-secondary)' }}>Paid</th>
                <th style={{ textAlign: 'right', padding: '14px 16px', fontSize: '0.78rem', letterSpacing: '0.03em', color: 'var(--text-secondary)' }}>Patient Resp.</th>
                <th style={{ textAlign: 'left', padding: '14px 16px', fontSize: '0.78rem', letterSpacing: '0.03em', color: 'var(--text-secondary)' }}>Adjustments</th>
              </tr>
            </thead>
            <tbody>
              {!isLoading && claims.length === 0 && (
                <tr>
                  <td colSpan={7} style={{ padding: '26px 16px', color: 'var(--text-secondary)', textAlign: 'center' }}>
                    No claims found in the selected remittance file.
                  </td>
                </tr>
              )}

              {claims.map((claim) => {
                const isExpanded = !!expandedRows[claim.key];

                return (
                  <React.Fragment key={claim.key}>
                    <tr style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                      <td style={{ padding: '14px 16px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <button
                            type="button"
                            onClick={() => claim.hasAdjustments && toggleExpand(claim.key)}
                            disabled={!claim.hasAdjustments}
                            style={{
                              width: '24px',
                              height: '24px',
                              borderRadius: '6px',
                              border: '1px solid rgba(255,255,255,0.15)',
                              background: claim.hasAdjustments ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.02)',
                              color: claim.hasAdjustments ? 'var(--text-primary)' : 'var(--text-secondary)',
                              display: 'inline-flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              cursor: claim.hasAdjustments ? 'pointer' : 'not-allowed',
                            }}
                            aria-label={claim.hasAdjustments ? 'Toggle adjustments' : 'No adjustments'}
                          >
                            {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                          </button>

                          <span style={{ fontFamily: 'monospace', fontWeight: 700 }}>{claim.claimId}</span>
                        </div>
                      </td>

                      <td style={{ padding: '14px 16px' }}>{claim.patientName}</td>

                      <td style={{ padding: '14px 16px' }}>
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            padding: '4px 10px',
                            borderRadius: '999px',
                            fontSize: '0.76rem',
                            fontWeight: 700,
                            color: claim.statusMeta.color,
                            background: claim.statusMeta.bg,
                            border: `1px solid ${claim.statusMeta.border}`,
                          }}
                        >
                          {claim.statusMeta.label}
                        </span>
                      </td>

                      <td style={{ padding: '14px 16px', textAlign: 'right', fontFamily: 'monospace' }}>
                        ${claim.billedAmount.toLocaleString()}
                      </td>

                      <td style={{ padding: '14px 16px', textAlign: 'right', fontFamily: 'monospace', color: '#1E8E3E', fontWeight: 700 }}>
                        ${claim.paidAmount.toLocaleString()}
                      </td>

                      <td style={{ padding: '14px 16px', textAlign: 'right', fontFamily: 'monospace' }}>
                        ${claim.patientResponsibility.toLocaleString()}
                      </td>

                      <td style={{ padding: '14px 16px' }}>
                        {claim.hasAdjustments ? (
                          <span style={{ color: '#f59e0b', fontWeight: 700 }}>
                            {claim.adjustments.length} Adjustment{claim.adjustments.length !== 1 ? 's' : ''}
                          </span>
                        ) : (
                          <span style={{ color: 'var(--text-secondary)' }}>None</span>
                        )}
                      </td>
                    </tr>

                    {isExpanded && claim.adjustments.map((adjustment, adjIndex) => (
                      <tr key={`${claim.key}_adj_${adjIndex}`} style={{ background: 'rgba(245, 158, 11, 0.05)' }}>
                        <td style={{ padding: '12px 16px 12px 48px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <AlertTriangle size={14} color="var(--text-secondary)" />
                            <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Adjustment</span>
                          </div>
                        </td>
                        
                        <td style={{ padding: '12px 16px' }}>
                          <span style={{ fontFamily: 'monospace' }}>
                            {adjustment.groupCode}-{adjustment.reasonCode}
                          </span>
                        </td>
                        
                        <td style={{ padding: '12px 16px' }}>
                          <button
                            onClick={() => explainAdjustment(adjustment.reasonCode)}
                            style={{
                              padding: '4px 8px',
                              fontSize: '0.75rem',
                              backgroundColor: '#00D6FF',
                              color: '#000',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              fontWeight: 600
                            }}
                          >
                            Explain
                          </button>
                        </td>
                        
                        <td colSpan={2} style={{ padding: '12px 16px', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                          {adjustment.explanation || 'Click "Explain" for AI explanation'}
                        </td>
                        
                        <td style={{ padding: '12px 16px', textAlign: 'right', fontFamily: 'monospace', color: '#f59e0b', fontWeight: 700 }}>
                          -${Math.abs(adjustment.amount).toLocaleString()}
                        </td>
                        
                        <td></td>
                      </tr>
                    ))}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}