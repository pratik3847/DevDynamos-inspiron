import React, { useState, useEffect, useMemo } from 'react';
import { Upload, FileText, DollarSign, Users, AlertTriangle, Filter, ChevronDown, ChevronRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface ParsedFile {
  file_id: string;
  filename: string;
  uploaded_at: string;
  status: string;
  parsed_data?: any;
}

interface ClaimRecord {
  key: string;
  claimId: string;
  patientName: string;
  billedAmount: number;
  paidAmount: number;
  patientResponsibility: number;
  statusCode: string;
  statusLabel: string;
  statusColor: string;
  adjustments: AdjustmentRecord[];
  hasAdjustments: boolean;
}

interface AdjustmentRecord {
  groupCode: string;
  reasonCode: string;
  amount: number;
  explanation?: string;
}

const STATUS_MAP: Record<string, { label: string; color: string; bg: string; border: string }> = {
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

const DEFAULT_STATUS = {
  label: 'Unknown Status',
  color: 'var(--text-secondary)',
  bg: 'rgba(127, 127, 127, 0.12)',
  border: 'rgba(127, 127, 127, 0.3)',
};

export default function Parser835Dashboard() {
  const { user } = useAuth();
  const [files, setFiles] = useState<ParsedFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<ParsedFile | null>(null);
  const [loading, setLoading] = useState(false);
  const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});
  const [showAdjustedOnly, setShowAdjustedOnly] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/parser/files', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setFiles(data.files || []);
        
        // Auto-select the most recent file if available
        if (data.files?.length > 0 && !selectedFile) {
          handleFileSelect(data.files[0]);
        }
      }
    } catch (error) {
      console.error('Error fetching files:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = async (file: ParsedFile) => {
    setSelectedFile(file);
    if (file.status === 'uploaded') {
      await parseFile(file.file_id);
    }
  };

  const parseFile = async (fileId: string) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/parser/parse/${fileId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSelectedFile(prev => prev ? { ...prev, parsed_data: data, status: 'parsed' } : null);
        await fetchFiles();
      }
    } catch (error) {
      console.error('Error parsing file:', error);
    }
  };

  const handleFileUpload = async (file: File) => {
    setLoading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/parser/upload-835', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        await fetchFiles();
        
        const newFile = { ...data, status: 'uploaded' };
        handleFileSelect(newFile);
      } else {
        throw new Error('Upload failed');
      }
    } catch (error) {
      console.error('Error uploading file:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const parseClaimsFromData = (parsedData: any): ClaimRecord[] => {
    if (!parsedData?.claims) return [];

    return parsedData.claims.map((claim: any, index: number) => {
      const statusMeta = STATUS_MAP[claim.claim_status_code] || DEFAULT_STATUS;
      
      const adjustments = claim.adjustments?.map((adj: any) => ({
        groupCode: adj.group_code,
        reasonCode: adj.reason_code,
        amount: adj.adjustment_amount,
        explanation: adj.explanation
      })) || [];

      return {
        key: `claim_${index}_${claim.claim_control_number}`,
        claimId: claim.claim_control_number,
        patientName: claim.patient_name || 'Unknown Patient',
        billedAmount: parseFloat(claim.total_billed_amount) || 0,
        paidAmount: parseFloat(claim.total_paid_amount) || 0,
        patientResponsibility: parseFloat(claim.patient_responsibility_amount) || 0,
        statusCode: claim.claim_status_code,
        statusLabel: statusMeta.label,
        statusColor: statusMeta.color,
        adjustments,
        hasAdjustments: adjustments.length > 0,
      };
    });
  };

  const claims = useMemo(() => {
    const allClaims = parseClaimsFromData(selectedFile?.parsed_data);
    
    if (!showAdjustedOnly) return allClaims;
    
    return allClaims.filter(claim => claim.hasAdjustments);
  }, [selectedFile?.parsed_data, showAdjustedOnly]);

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
          context: `Claim adjustment in remittance file ${selectedFile?.filename}`
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

  // If no file is selected, show upload interface similar to 834 dashboard
  if (!selectedFile) {
    return (
      <div className="dash-card" style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <h2 style={{ marginBottom: '8px' }}>835 Remittance Parser</h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
          Upload/select an 835 EDI file to parse payment remittance data with AI explanations.
        </p>

        <div 
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          style={{
            border: `2px dashed ${dragActive ? '#00D6FF' : 'rgba(255,255,255,0.3)'}`,
            borderRadius: '12px',
            padding: '40px',
            textAlign: 'center',
            backgroundColor: dragActive ? 'rgba(0, 214, 255, 0.05)' : 'transparent',
            transition: 'all 0.3s ease',
            marginBottom: '24px'
          }}
        >
          <Upload size={48} color={dragActive ? '#00D6FF' : 'var(--text-secondary)'} style={{ marginBottom: '16px', display: 'block', margin: '0 auto 16px' }} />
          <h3 style={{ marginBottom: '8px', fontWeight: 600 }}>Upload 835 EDI File</h3>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>
            Drag and drop your 835 remittance file here, or click to browse
          </p>
          <input
            type="file"
            accept=".txt,.edi,.x12"
            onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
            style={{ display: 'none' }}
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            style={{
              display: 'inline-block',
              padding: '10px 20px',
              backgroundColor: '#00D6FF',
              color: '#000',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: 600
            }}
          >
            Choose File
          </label>
          
          {loading && (
            <div style={{ marginTop: '16px' }}>
              <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                Processing file...
              </div>
            </div>
          )}
        </div>

        {files.length > 0 && (
          <div>
            <h4 style={{ marginBottom: '12px', fontWeight: 600 }}>Recent Files</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {files.slice(0, 5).map((file) => (
                <div
                  key={file.file_id}
                  onClick={() => handleFileSelect(file)}
                  style={{
                    padding: '12px 16px',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    transition: 'all 0.3s ease'
                  }}
                >
                  <FileText size={16} color="var(--text-secondary)" />
                  <div style={{ flex: 1, textAlign: 'left' }}>
                    <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{file.filename}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                      {new Date(file.uploaded_at).toLocaleDateString()}
                    </div>
                  </div>
                  <div style={{
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    backgroundColor: file.status === 'parsed' ? 'rgba(30, 142, 62, 0.14)' : 'rgba(179, 107, 0, 0.14)',
                    color: file.status === 'parsed' ? '#1E8E3E' : '#B36B00'
                  }}>
                    {file.status}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // Main dashboard view with 834-style layout
  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px', flexWrap: 'wrap' }}>
        <div>
          <h1 style={{ fontSize: '1.55rem', fontWeight: 700, marginBottom: '8px' }}>835 Remittance Analysis</h1>
          <p style={{ color: 'var(--text-secondary)' }}>
            File: <strong>{selectedFile.filename}</strong> - Payment remittance with claim-level details and AI explanations.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
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
          
          <button
            onClick={() => setSelectedFile(null)}
            style={{
              padding: '8px 16px',
              backgroundColor: 'transparent',
              border: '1px solid rgba(255,255,255,0.2)',
              color: 'var(--text-secondary)',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '0.875rem'
            }}
          >
            Upload New File
          </button>
        </div>
      </div>

      {/* Statistics Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
        <div className="dash-card" style={{ padding: '16px' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Total Claims</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 700 }}>{loading ? '...' : totalClaims}</div>
        </div>
        <div className="dash-card" style={{ padding: '16px' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Total Billed</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 700 }}>{loading ? '...' : `$${totalBilled.toLocaleString()}`}</div>
        </div>
        <div className="dash-card" style={{ padding: '16px' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Total Paid</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 700, color: '#1E8E3E' }}>{loading ? '...' : `$${totalPaid.toLocaleString()}`}</div>
        </div>
        <div className="dash-card" style={{ padding: '16px' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Claims with Adjustments</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 700, color: '#f59e0b' }}>{loading ? '...' : totalAdjustments}</div>
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
              {!loading && claims.length === 0 && (
                <tr>
                  <td colSpan={7} style={{ padding: '26px 16px', color: 'var(--text-secondary)', textAlign: 'center' }}>
                    No claims found in the selected remittance file.
                  </td>
                </tr>
              )}

              {claims.map((claim) => {
                const isExpanded = !!expandedRows[claim.key];
                const statusMeta = STATUS_MAP[claim.statusCode] || DEFAULT_STATUS;

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
                            color: statusMeta.color,
                            background: statusMeta.bg,
                            border: `1px solid ${statusMeta.border}`,
                          }}
                        >
                          {statusMeta.label}
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