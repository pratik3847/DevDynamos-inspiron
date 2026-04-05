import React, { useEffect, useMemo, useState } from 'react';
import { UploadCloud, File, FileText, CheckCircle2, Trash2 } from 'lucide-react';
import { api } from '../services/api';
import { useSession } from '../context/SessionContext';
import { Session } from '../services/types';

export default function Upload() {
  const [isUploading, setIsUploading] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [selectedSessionDetail, setSelectedSessionDetail] = useState<Session | null>(null);
  const [isLoadingSelected, setIsLoadingSelected] = useState(false);
  const [isLoadingSessions, setIsLoadingSessions] = useState(true);
  const { setActiveSessionId } = useSession();

  const toErrorMessage = (err: unknown): string => {
    const msg = err instanceof Error ? err.message : String(err || 'Unknown error');
    const lower = msg.toLowerCase();
    if (lower.includes('failed to fetch') || lower.includes('networkerror')) {
      return 'Backend is unreachable. Please ensure the API server is running on port 8000.';
    }
    return msg;
  };

  const extractEdiMetadata = (session: Session | null) => {
    const segments: any[] = session?.parsedJson?.segments ?? [];

    const findSegment = (id: string) => segments.find(s => s?.segmentId === id) || null;
    const getEl = (seg: any, oneBasedIndex: number) => {
      const el = seg?.elements?.[oneBasedIndex - 1];
      return (el?.value ?? '').toString().trim();
    };

    const isa = findSegment('ISA');
    const gs = findSegment('GS');

    const senderId = isa ? getEl(isa, 6) : '';
    const receiverId = isa ? getEl(isa, 8) : '';
    const isaDate = isa ? getEl(isa, 9) : '';
    const functionalGroup = gs ? getEl(gs, 1) : '';

    const parseYYMMDD = (yyMMdd: string) => {
      const v = (yyMMdd || '').trim();
      if (!/^\d{6}$/.test(v)) return '';
      const yy = parseInt(v.slice(0, 2), 10);
      const mm = v.slice(2, 4);
      const dd = v.slice(4, 6);
      const year = yy < 70 ? 2000 + yy : 1900 + yy;
      return `${year}-${mm}-${dd}`;
    };

    return {
      senderId: senderId || '-',
      receiverId: receiverId || '-',
      interchangeDate: parseYYMMDD(isaDate) || isaDate || '-',
      functionalGroup: functionalGroup || '-',
    };
  };

  const meta = useMemo(() => extractEdiMetadata(selectedSessionDetail), [selectedSessionDetail]);

  const loadSelectedSession = async (sessionId: string) => {
    setIsLoadingSelected(true);
    setErrorMessage(null);
    try {
      const full = await api.getSession(sessionId);
      setSelectedSessionDetail(full);
    } catch (e) {
      setErrorMessage(toErrorMessage(e));
      setSelectedSessionDetail(null);
    } finally {
      setIsLoadingSelected(false);
    }
  };

  useEffect(() => {
    const load = async () => {
      setErrorMessage(null);
      try {
        const data = await api.getSessions();
        setSessions(data);
        const firstId = data[0]?.id ?? null;
        setSelectedSessionId(firstId);
        if (firstId) {
          await loadSelectedSession(firstId);
        }
      } catch (e) {
        setErrorMessage(toErrorMessage(e));
      } finally {
        setIsLoadingSessions(false);
      }
    };
    load();
  }, []);

  const handleSelect = (sessionId: string) => {
    setSelectedSessionId(sessionId);
    setActiveSessionId(sessionId);
    loadSelectedSession(sessionId);
  };

  const handleDelete = async (sessionId: string) => {
    setErrorMessage(null);
    try {
      await api.deleteSession(sessionId);
      setSessions(prev => {
        const next = prev.filter(s => s.id !== sessionId);

        if (selectedSessionId === sessionId) {
          const nextId = next[0]?.id ?? null;
          setSelectedSessionId(nextId);
          setSelectedSessionDetail(null);
          if (nextId) {
            setActiveSessionId(nextId);
            void loadSelectedSession(nextId);
          }
        }

        return next;
      });
    } catch (e) {
      setErrorMessage(toErrorMessage(e));
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setIsUploading(true);
      setErrorMessage(null);
      try {
        const sessionPayload = await api.uploadFile(e.target.files[0]);
        setSessions(prev => [sessionPayload, ...prev]);
        setSelectedSessionId(sessionPayload.id);
        setSelectedSessionDetail(sessionPayload);
        setActiveSessionId(sessionPayload.id);
        await loadSelectedSession(sessionPayload.id);
      } catch (err) {
        setErrorMessage(toErrorMessage(err));
      } finally {
        setIsUploading(false);
      }
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '8px' }}>Upload Files</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '32px' }}>Import EDI files for processing. Supports .edi, .txt, .dat, .x12, and ZIP batch files.</p>

      {errorMessage && (
        <div
          role="alert"
          className="dash-card"
          style={{
            marginBottom: '16px',
            border: '1px solid rgba(255, 99, 99, 0.45)',
            background: 'rgba(255, 99, 99, 0.1)',
            color: '#ffd0d0',
            fontSize: '0.9rem',
          }}
        >
          {errorMessage}
        </div>
      )}

      <div
        className="dash-card"
        style={{
          border: '2px dashed rgba(255,255,255,0.1)',
          background: 'rgba(0,0,0,0.2)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          padding: '60px 20px',
          marginBottom: '24px',
          cursor: 'pointer',
          position: 'relative'
        }}
      >
        <input
          type="file"
          onChange={handleUpload}
          style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', opacity: 0, cursor: 'pointer' }}
          disabled={isUploading}
        />
        <div style={{ width: '48px', height: '48px', background: 'rgba(255,255,255,0.05)', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
          <UploadCloud size={24} color="var(--text-secondary)" />
        </div>
        <div style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '8px' }}>{isUploading ? 'Processing File...' : 'Drag and drop files here'}</div>
        <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '16px' }}>or click to browse</div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <span style={{ fontSize: '0.75rem', background: 'rgba(255,255,255,0.1)', padding: '4px 8px', borderRadius: '4px' }}>.edi</span>
          <span style={{ fontSize: '0.75rem', background: 'rgba(255,255,255,0.1)', padding: '4px 8px', borderRadius: '4px' }}>.txt</span>
          <span style={{ fontSize: '0.75rem', background: 'rgba(255,255,255,0.1)', padding: '4px 8px', borderRadius: '4px' }}>.dat</span>
          <span style={{ fontSize: '0.75rem', background: 'rgba(255,255,255,0.1)', padding: '4px 8px', borderRadius: '4px' }}>.x12</span>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        <div className="dash-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Uploaded Files</h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{sessions.length} files</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {isLoadingSessions ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)' }}>Loading uploaded files…</div>
            ) : sessions.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)' }}>No documents uploaded.</div>
            ) : (
              sessions.map((s) => {
                const isSelected = s.id === selectedSessionId;
                return (
                  <div
                    key={s.id}
                    onClick={() => handleSelect(s.id)}
                    role="button"
                    tabIndex={0}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '16px',
                      background: isSelected ? 'rgba(97, 107, 184, 0.79)' : 'rgba(255,255,255,0.05)',
                      border: isSelected ? '1px solid rgba(0, 80, 255, 0.2)' : '1px solid transparent',
                      padding: '16px',
                      borderRadius: '12px',
                      cursor: 'pointer'
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') handleSelect(s.id);
                    }}
                  >
                    <FileText color={isSelected ? '#0050FF' : 'var(--text-secondary)'} size={20} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 600, fontSize: '0.9375rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.filename}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{new Date(s.uploadDate).toLocaleString()}</div>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(s.id);
                      }}
                      style={{
                        background: 'transparent',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '10px',
                        padding: '8px',
                        cursor: 'pointer'
                      }}
                      aria-label={`Delete ${s.filename}`}
                      title="Delete"
                    >
                      <Trash2 size={16} color={'var(--text-secondary)'} />
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </div>

        <div className="dash-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '24px' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>File Metadata</h3>
            {selectedSessionDetail && (
              <span style={{ fontSize: '0.75rem', background: 'rgba(0, 80, 255, 0.2)', color: 'var(--text-secondary)', padding: '4px 8px', borderRadius: '4px' }}>
                {selectedSessionDetail.status}
              </span>
            )}
          </div>

          {!selectedSessionId ? (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)' }}>Upload an EDI file to extract transmission metadata.</div>
          ) : isLoadingSelected ? (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)' }}>Loading metadata…</div>
          ) : !selectedSessionDetail ? (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)' }}>Unable to load metadata for this file.</div>
          ) : (
            <>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', paddingBottom: '24px', borderBottom: '1px solid rgba(255,255,255,0.1)', marginBottom: '24px' }}>
                <div style={{ width: '40px', height: '40px', background: 'rgba(0, 80, 255, 0.1)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <File color="#0050FF" />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600 }}>{selectedSessionDetail.filename}</div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>{selectedSessionDetail.id}</div>
                </div>
                <CheckCircle2 color="#34C759" />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <FileText size={12} /> Sender ID
                  </div>
                  <div style={{ fontWeight: 600 }}>{meta.senderId}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <FileText size={12} /> Receiver ID
                  </div>
                  <div style={{ fontWeight: 600 }}>{meta.receiverId}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <FileText size={12} /> Interchange Date
                  </div>
                  <div style={{ fontWeight: 600 }}>{meta.interchangeDate}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <FileText size={12} /> Functional Group
                  </div>
                  <div style={{ fontWeight: 600 }}>{meta.functionalGroup}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <FileText size={12} /> Uploaded
                  </div>
                  <div style={{ fontWeight: 600 }}>{new Date(selectedSessionDetail.uploadDate).toLocaleString()}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <FileText size={12} /> Errors / Fixes
                  </div>
                  <div style={{ fontWeight: 600 }}>{(selectedSessionDetail.errors?.length ?? 0)} / {(selectedSessionDetail.fixes?.length ?? 0)}</div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
