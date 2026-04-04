import React, { useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Download,
  RefreshCw,
  Sparkles,
  Wand2,
} from 'lucide-react';
import { useSession } from '../context/SessionContext';
import { api } from '../services/api';
import { FixSuggestion } from '../services/types';

export default function FixAssistant() {
  const { activeSession, isLoading, refreshSession } = useSession();
  const [isFixing, setIsFixing] = useState<string | null>(null);
  const [isFixingAll, setIsFixingAll] = useState<boolean>(false);
  const [isDownloading, setIsDownloading] = useState<'edi' | 'report' | null>(null);
  const [applyError, setApplyError] = useState<string | null>(null);

  useEffect(() => {
    // Ensure we pick up server-side regenerated fixes for older sessions.
    // (No-op if there is no active session id)
    refreshSession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!activeSession) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          color: 'var(--text-secondary)',
        }}
      >
        <Sparkles size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
        <h3>No Active Session</h3>
        <p>Please upload a file to view fix suggestions.</p>
      </div>
    );
  }

  const fixes = activeSession.fixes || [];
  const errors = activeSession.errors || [];

  const appliedFixesCount = fixes.filter((f) => f.status === 'accepted').length;
  const pendingFixes = fixes.filter((f) => f.status !== 'accepted');
  const pendingFixesCount = pendingFixes.length;

  const fixableErrorIds = useMemo(() => new Set((fixes || []).map((f) => String(f.errorId || ''))), [fixes]);
  const notAutoFixableCount = useMemo(() => {
    const uniqueErrors = new Set((errors || []).map((e) => String(e.id || '')));
    let count = 0;
    for (const id of uniqueErrors) {
      if (!id) continue;
      if (!fixableErrorIds.has(id)) count += 1;
    }
    return count;
  }, [errors, fixableErrorIds]);

  const manualIssues = useMemo(() => {
    return (errors || []).filter((e) => !fixableErrorIds.has(String(e.id || '')));
  }, [errors, fixableErrorIds]);

  const avgConfidence = useMemo(() => {
    const nums = (pendingFixes || [])
      .map((f) => (typeof f.confidenceScore === 'number' ? f.confidenceScore : null))
      .filter((n): n is number => typeof n === 'number' && Number.isFinite(n));
    if (nums.length === 0) return null;
    return Math.round(nums.reduce((a, b) => a + b, 0) / nums.length);
  }, [pendingFixes]);

  const handleApplyFix = async (fix: FixSuggestion) => {
    if (!activeSession?.id || !fix?.id) return;
    setIsFixing(fix.id);
    setApplyError(null);
    try {
      await api.applyFix(activeSession.id, fix);
      await refreshSession();
    } catch (err) {
      console.error('Failed to apply fix', err);
      setApplyError(err instanceof Error ? err.message : 'Failed to apply fix');
    } finally {
      setIsFixing(null);
    }
  };

  const handleAutoFixAll = async () => {
    if (!activeSession?.id) return;
    const toApply = (activeSession.fixes || []).filter(
      (f) =>
        f.status !== 'accepted' &&
        f.id &&
        (f.auto_apply === true) &&
        f.suggested !== ''
    );
    if (toApply.length === 0) return;

    setIsFixingAll(true);
    setApplyError(null);
    try {
      await api.applyFixBatch(activeSession.id, toApply);
      await refreshSession();
    } catch (err) {
      console.error('Failed to auto-fix all', err);
      setApplyError(err instanceof Error ? err.message : 'Failed to auto-fix all');
    } finally {
      setIsFixingAll(false);
    }
  };

  return (
    <div className="edi-page">
      <div className="edi-page__header">
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '8px' }}>Fix Assistant</h1>
          <p style={{ color: 'var(--text-secondary)' }}>Auto-fix validation issues and export corrected files</p>
        </div>
        <div className="edi-page__actions">
          <button
            className="btn outline"
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
            onClick={handleAutoFixAll}
            disabled={!activeSession?.id || isFixingAll || pendingFixesCount === 0}
            title={pendingFixesCount === 0 ? 'No pending auto-fixes available' : 'Apply all pending auto-fixes'}
          >
            <Wand2 size={16} /> {isFixingAll ? 'Auto-Fixing...' : 'Auto Fix All'}
          </button>
          <button
            className="btn outline"
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
            onClick={refreshSession}
            disabled={isLoading}
          >
            <RefreshCw size={16} /> {isLoading ? 'Syncing...' : 'Sync'}
          </button>
        </div>
      </div>

      <div className="dash-card" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div
              style={{
                width: '48px',
                height: '48px',
                borderRadius: '50%',
                background: 'rgba(0, 214, 255, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Sparkles size={24} color="#00D6FF" />
            </div>
            <div>
              <div style={{ fontSize: '1.125rem', fontWeight: 600 }}>Fix Summary</div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                {pendingFixesCount} pending auto-fixes · {errors.length} validation issues
              </div>
            </div>
          </div>
        </div>

        <div className="edi-grid edi-grid--4" style={{ gap: '16px' }}>
          <div
            style={{
              background: 'rgba(52, 199, 89, 0.05)',
              border: '1px solid rgba(52, 199, 89, 0.1)',
              padding: '16px',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
            }}
          >
            <CheckCircle2 color="#34C759" size={20} />
            <div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#34C759' }}>{appliedFixesCount}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Fixed</div>
            </div>
          </div>

          <div
            style={{
              background: 'rgba(0, 80, 255, 0.05)',
              border: '1px solid rgba(0, 80, 255, 0.1)',
              padding: '16px',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
            }}
          >
            <RefreshCw color="#0050FF" size={20} />
            <div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0050FF' }}>{pendingFixesCount}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Pending</div>
            </div>
          </div>

          <div
            style={{
              background: 'rgba(255, 149, 0, 0.05)',
              border: '1px solid rgba(255, 149, 0, 0.1)',
              padding: '16px',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
            }}
          >
            <AlertTriangle color="#FF9500" size={20} />
            <div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#FF9500' }}>{notAutoFixableCount}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Not Auto-Fixable</div>
            </div>
          </div>

          <div
            style={{
              background: 'rgba(0, 214, 255, 0.05)',
              border: '1px solid rgba(0, 214, 255, 0.1)',
              padding: '16px',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
            }}
          >
            <Sparkles color="#00D6FF" size={20} />
            <div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#00D6FF' }}>{avgConfidence === null ? '—' : `${avgConfidence}%`}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Avg Confidence</div>
            </div>
          </div>
        </div>
      </div>

      <div className="edi-split edi-split--equal">
        {/* Left Pane - AI Suggestions */}
        <div className="dash-card edi-panel">
          <div className="edi-panel__header">
            <h3 style={{ fontSize: '1rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
              <Sparkles size={16} color="#00D6FF" /> Auto Fix Suggestions
            </h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{pendingFixesCount} pending</span>
          </div>

          <div className="edi-panel__body custom-scrollbar">
            {applyError ? (
              <div
                style={{
                  background: 'rgba(255, 59, 48, 0.08)',
                  border: '1px solid rgba(255, 59, 48, 0.18)',
                  borderRadius: '12px',
                  padding: '12px 14px',
                  marginBottom: '16px',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '10px',
                }}
              >
                <AlertCircle size={16} color="var(--accent-red)" />
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontWeight: 700, marginBottom: '2px' }}>Auto Fix failed</div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>{applyError}</div>
                </div>
              </div>
            ) : null}
            {pendingFixesCount === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                No automated fixes available. Review issues in Validation.
              </div>
            ) : (
              pendingFixes.map((fix, idx) => {
                const linkedError = (activeSession.errors || []).find((e) => String(e.id) === String(fix.errorId));
                const canApply = Boolean(fix.id) && (fix.suggested !== '' || String(fix.operation || '').toUpperCase() === 'INSERT_NM1_82_FROM_85');
                return (
                  <div
                    key={idx}
                    style={{
                      background: 'var(--surface-2)',
                      border: '1px solid var(--surface-border-muted)',
                      borderRadius: '12px',
                      padding: '16px',
                      marginBottom: '16px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0 }}>
                        <span style={{ color: 'var(--accent-cyan)', fontWeight: 700, fontSize: '0.875rem' }}>{fix.errorId}</span>
                        <span style={{ fontSize: '0.875rem', fontWeight: 600 }}>{fix.action || 'Auto Fix'}</span>
                        {linkedError?.segment ? (
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                            Segment: {linkedError.segment}
                            {linkedError.element ? ` · ${linkedError.element}` : ''}
                          </span>
                        ) : null}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-cyan)', fontSize: '0.875rem', fontWeight: 700 }}>
                        <Sparkles size={14} /> {typeof fix.confidenceScore === 'number' ? `${fix.confidenceScore}%` : fix.confidence}
                      </div>
                    </div>

                    {linkedError ? (
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'flex-start',
                          gap: '10px',
                          background: 'var(--surface-3)',
                          border: '1px solid var(--surface-border-muted)',
                          padding: '12px',
                          borderRadius: '10px',
                          marginBottom: '12px',
                        }}
                      >
                        {linkedError.severity === 'Warning' ? <AlertTriangle size={16} color="var(--accent-red)" /> : <AlertCircle size={16} color="var(--accent-red)" />}
                        <div style={{ minWidth: 0 }}>
                          <div style={{ fontWeight: 700, marginBottom: '4px' }}>Validation Issue</div>
                          <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>{linkedError.description}</div>
                        </div>
                      </div>
                    ) : null}

                    <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>{fix.description || 'Suggested fix available.'}</p>

                    {fix.reasoning ? (
                      <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '12px' }}>
                        <span style={{ fontWeight: 700 }}>Reasoning:</span> {fix.reasoning}
                      </div>
                    ) : null}

                    <div className="edi-replacement-grid" style={{ marginBottom: '16px' }}>
                      <div style={{ background: 'rgba(255, 59, 48, 0.1)', border: '1px solid rgba(255, 59, 48, 0.2)', padding: '12px', borderRadius: '8px' }}>
                        <div style={{ fontSize: '0.75rem', color: '#FF3B30', marginBottom: '4px' }}>Current Value</div>
                        <div style={{ color: '#FF3B30', fontFamily: 'monospace' }}>{fix.original !== '' ? fix.original : '(unavailable)'}</div>
                      </div>
                      <div className="edi-replacement-arrow">
                        <ChevronRight size={16} color="var(--text-secondary)" />
                      </div>
                      <div style={{ background: 'rgba(52, 199, 89, 0.1)', border: '1px solid rgba(52, 199, 89, 0.2)', padding: '12px', borderRadius: '8px' }}>
                        <div style={{ fontSize: '0.75rem', color: '#34C759', marginBottom: '4px' }}>Replacement</div>
                        <div style={{ color: '#34C759', fontFamily: 'monospace' }}>{fix.suggested !== '' ? fix.suggested : '(unavailable)'}</div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                      <button
                        className="btn primary"
                        style={{ padding: '6px 16px', fontSize: '0.75rem' }}
                        onClick={() => handleApplyFix(fix)}
                        disabled={isFixing === fix.id || !canApply}
                      >
                        {isFixing === fix.id ? 'Applying...' : 'Auto Fix'}
                      </button>
                    </div>
                  </div>
                );
              })
            )}

            {manualIssues.length > 0 ? (
              <div style={{ marginTop: '8px' }}>
                <div style={{ fontWeight: 700, margin: '12px 0 8px 0' }}>Manual Review Needed</div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '12px' }}>
                  These validation issues don’t have a safe auto-fix yet.
                </div>
                {manualIssues.map((e, i) => (
                  <div
                    key={`${e.id}_${i}`}
                    style={{
                      background: 'var(--surface-2)',
                      border: '1px solid var(--surface-border-muted)',
                      borderRadius: '12px',
                      padding: '12px',
                      marginBottom: '10px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'flex-start' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
                        {e.severity === 'Warning' ? <AlertTriangle size={16} color="var(--accent-red)" /> : <AlertCircle size={16} color="var(--accent-red)" />}
                        <div style={{ minWidth: 0 }}>
                          <div style={{ fontWeight: 700, fontSize: '0.875rem' }}>{e.id}</div>
                          <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>{e.description}</div>
                        </div>
                      </div>
                      <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', whiteSpace: 'nowrap' }}>
                        {e.segment ? `Segment: ${e.segment}` : ''}
                        {e.element ? ` · ${e.element}` : ''}
                      </div>
                    </div>
                    <div style={{ marginTop: '8px', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                      Auto-fix suggestion: (not available)
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        </div>

        {/* Right Pane - Export */}
        <div className="dash-card edi-panel">
          <div className="edi-panel__header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <Download size={16} />
              <h3 style={{ fontSize: '1rem', fontWeight: 600, margin: 0 }}>Export Files</h3>
            </div>
          </div>

          <div className="edi-panel__body custom-scrollbar">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ background: 'var(--surface-2)', border: '1px solid var(--surface-border-muted)', borderRadius: '12px', padding: '16px' }}>
                <div style={{ fontWeight: 600, marginBottom: '6px' }}>Updated EDI</div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '12px' }}>
                  Export the latest corrected EDI for this session.
                </div>
                <button
                  className="btn outline"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
                  onClick={async () => {
                    if (!activeSession?.id) return;
                    setIsDownloading('edi');
                    try {
                      await api.downloadSessionEdi(activeSession.id);
                    } finally {
                      setIsDownloading(null);
                    }
                  }}
                  disabled={!activeSession?.id || isDownloading === 'edi'}
                >
                  <Download size={16} /> {isDownloading === 'edi' ? 'Downloading...' : 'Export Updated EDI'}
                </button>
              </div>

              <div style={{ background: 'var(--surface-2)', border: '1px solid var(--surface-border-muted)', borderRadius: '12px', padding: '16px' }}>
                <div style={{ fontWeight: 600, marginBottom: '6px' }}>Validation + Suggestions Report</div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '12px' }}>
                  Export a combined report including validation issues, auto-fix suggestions, and applied fix audit.
                </div>
                <button
                  className="btn outline"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
                  onClick={async () => {
                    if (!activeSession?.id) return;
                    setIsDownloading('report');
                    try {
                      await api.downloadSessionReport(activeSession.id);
                    } finally {
                      setIsDownloading(null);
                    }
                  }}
                  disabled={!activeSession?.id || isDownloading === 'report'}
                >
                  <Download size={16} /> {isDownloading === 'report' ? 'Downloading...' : 'Export Report'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
