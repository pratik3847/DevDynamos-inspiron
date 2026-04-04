import React, { useEffect, useMemo, useState } from 'react';
import { FileText, CheckCircle, AlertTriangle, AlertCircle, UploadCloud, CheckSquare, Wrench, Download } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Session } from '../services/types';

export default function DashboardHome() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const data = await api.getSessions();
        if (!mounted) return;
        setSessions(data);
        setLoadError(null);
      } catch (err) {
        if (!mounted) return;
        setLoadError('Unable to load dashboard data.');
      } finally {
        if (mounted) setLoading(false);
      }
    };
    load();
    return () => {
      mounted = false;
    };
  }, []);

  const metrics = useMemo(() => {
    const filesProcessed = sessions.length;
    const errorCount = sessions.reduce((acc, s) => acc + (s.originalErrors?.length ?? s.errors.length), 0);
    const attentionCount = sessions.filter((s) => (s.originalErrors?.length ?? s.errors.length) > 0).length;
    const cleanCount = sessions.filter((s) => (s.originalErrors?.length ?? s.errors.length) === 0).length;

    return {
      filesProcessed,
      errorCount,
      attentionCount,
      cleanCount,
    };
  }, [sessions]);

  const chartData = useMemo(() => {
    const days = 7;
    const today = new Date();
    const buckets: { key: string; label: string; count: number; errors: number }[] = [];

    for (let i = days - 1; i >= 0; i -= 1) {
      const d = new Date(today);
      d.setDate(today.getDate() - i);
      const key = d.toISOString().slice(0, 10);
      const label = d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
      buckets.push({ key, label, count: 0, errors: 0 });
    }

    const map = new Map(buckets.map((b) => [b.key, b]));
    for (const s of sessions) {
      const ts = new Date(s.uploadDate || s.createdAt || s.updatedAt || Date.now());
      const key = ts.toISOString().slice(0, 10);
      const bucket = map.get(key);
      if (!bucket) continue;
      bucket.count += 1;
      bucket.errors += s.originalErrors?.length ?? s.errors.length;
    }

    return buckets;
  }, [sessions]);

  const chart = useMemo(() => {
    const width = 640;
    const height = 220;
    const padX = 36;
    const padY = 24;
    const n = chartData.length;
    if (n === 0) return null;

    const maxValue = Math.max(1, ...chartData.map((d) => Math.max(d.count, d.errors)));

    const point = (idx: number, value: number) => {
      const x = n === 1 ? width / 2 : padX + (idx / (n - 1)) * (width - padX * 2);
      const y = height - padY - (value / maxValue) * (height - padY * 2);
      return { x, y };
    };

    const buildPath = (key: 'count' | 'errors') => {
      return chartData
        .map((d, idx) => {
          const p = point(idx, d[key]);
          return `${idx === 0 ? 'M' : 'L'} ${p.x} ${p.y}`;
        })
        .join(' ');
    };

    return {
      width,
      height,
      padX,
      padY,
      maxValue,
      countPath: buildPath('count'),
      errorPath: buildPath('errors'),
      points: chartData.map((d, idx) => ({
        count: point(idx, d.count),
        errors: point(idx, d.errors),
      })),
    };
  }, [chartData]);

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '8px' }}>Dashboard</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '32px' }}>Monitor your EDI processing pipeline and system health</p>

      {/* Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '24px', marginBottom: '24px' }}>
        <div className="dash-card">
          <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: 'rgba(0, 80, 255, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
            <FileText size={20} color="#0050FF" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '4px' }}>
            {loading ? '...' : metrics.filesProcessed}
          </div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Files Processed</div>
        </div>
        
        <div className="dash-card">
          <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: 'rgba(255, 149, 0, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
            <AlertTriangle size={20} color="#FF9500" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '4px' }}>
            {loading ? '...' : metrics.attentionCount}
          </div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Requires Attention</div>
        </div>

        <div className="dash-card">
          <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: 'rgba(255, 59, 48, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
            <AlertCircle size={20} color="#FF3B30" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '4px' }}>
            {loading ? '...' : metrics.errorCount}
          </div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Errors Found</div>
        </div>

        <div className="dash-card">
          <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: 'rgba(52, 199, 89, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
            <CheckCircle size={20} color="#34C759" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '4px' }}>
            {loading ? '...' : metrics.cleanCount}
          </div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Clean Sessions</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        {/* Chart View */}
        <div className="dash-card" style={{ display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '24px' }}>Processing Overview</h3>
          {loadError ? (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)', fontSize: '0.875rem', minHeight: '300px' }}>
              {loadError}
            </div>
          ) : loading ? (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)', fontSize: '0.875rem', minHeight: '300px' }}>
              Loading trends...
            </div>
          ) : sessions.length === 0 ? (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)', fontSize: '0.875rem', minHeight: '300px' }}>
              Upload files to see processing trends.
            </div>
          ) : (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '16px', minHeight: '300px' }}>
              <div style={{ display: 'flex', gap: '16px', alignItems: 'center', color: 'var(--text-secondary)', fontSize: '0.8125rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#0050FF', display: 'inline-block' }}></span>
                  Files processed
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#FF3B30', display: 'inline-block' }}></span>
                  Errors found
                </div>
              </div>

              {chart && (
                <svg viewBox={`0 0 ${chart.width} ${chart.height}`} style={{ width: '100%', height: '220px' }}>
                  {/* Grid lines + y-axis labels */}
                  {[0, 0.25, 0.5, 0.75, 1].map((t) => {
                    const y = chart.padY + (1 - t) * (chart.height - chart.padY * 2);
                    const value = Math.round(chart.maxValue * t);
                    return (
                      <g key={`grid-${t}`}>
                        <line
                          x1={chart.padX}
                          y1={y}
                          x2={chart.width - chart.padX}
                          y2={y}
                          stroke="rgba(255,255,255,0.08)"
                          strokeWidth="1"
                        />
                        <text
                          x={chart.padX - 8}
                          y={y + 4}
                          fill="rgba(255,255,255,0.45)"
                          fontSize="10"
                          textAnchor="end"
                        >
                          {value}
                        </text>
                      </g>
                    );
                  })}

                  {/* Lines */}
                  <path d={chart.countPath} fill="none" stroke="#0050FF" strokeWidth="2" />
                  <path d={chart.errorPath} fill="none" stroke="#FF3B30" strokeWidth="2" />

                  {/* Points */}
                  {chart.points.map((p, idx) => (
                    <g key={`pt-${idx}`}>
                      <circle cx={p.count.x} cy={p.count.y} r="3" fill="#0050FF" />
                      <circle cx={p.errors.x} cy={p.errors.y} r="3" fill="#FF3B30" />
                    </g>
                  ))}
                </svg>
              )}

              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                {chartData.map((d) => (
                  <span key={d.key}>{d.label}</span>
                ))}
              </div>

            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="dash-card">
          <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '24px' }}>Quick Actions</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div 
              onClick={() => navigate('/dashboard/upload')}
              style={{ display: 'flex', alignItems: 'center', gap: '16px', background: 'rgba(0, 80, 255, 0.05)', padding: '16px', borderRadius: '12px', cursor: 'pointer', border: '1px solid rgba(0, 80, 255, 0.1)' }}
            >
              <div style={{ background: 'rgba(0, 80, 255, 0.1)', padding: '8px', borderRadius: '8px' }}><UploadCloud size={16} color="#0050FF" /></div>
              <div style={{ flex: 1 }}>
                 <div style={{ fontWeight: 600, fontSize: '0.9375rem' }}>Upload Files</div>
                 <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Import EDI files for processing</div>
              </div>
            </div>

            <div 
              onClick={() => navigate('/dashboard/validation')}
              style={{ display: 'flex', alignItems: 'center', gap: '16px', background: 'rgba(52, 199, 89, 0.05)', padding: '16px', borderRadius: '12px', cursor: 'pointer', border: '1px solid rgba(52, 199, 89, 0.1)' }}
            >
              <div style={{ background: 'rgba(52, 199, 89, 0.1)', padding: '8px', borderRadius: '8px' }}><CheckSquare size={16} color="#34C759" /></div>
              <div style={{ flex: 1 }}>
                 <div style={{ fontWeight: 600, fontSize: '0.9375rem' }}>Validate Files</div>
                 <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Check files against rules</div>
              </div>
            </div>
            
            <div 
              onClick={() => navigate('/dashboard/fix-assistant')}
              style={{ display: 'flex', alignItems: 'center', gap: '16px', background: 'rgba(255, 149, 0, 0.05)', padding: '16px', borderRadius: '12px', cursor: 'pointer', border: '1px solid rgba(255, 149, 0, 0.1)' }}
            >
              <div style={{ background: 'rgba(255, 149, 0, 0.1)', padding: '8px', borderRadius: '8px' }}><Wrench size={16} color="#FF9500" /></div>
              <div style={{ flex: 1 }}>
                 <div style={{ fontWeight: 600, fontSize: '0.9375rem' }}>Fix Errors</div>
                 <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Auto-correct validation issues</div>
              </div>
            </div>

            <div 
              style={{ display: 'flex', alignItems: 'center', gap: '16px', background: 'rgba(0, 214, 255, 0.05)', padding: '16px', borderRadius: '12px', cursor: 'pointer', border: '1px solid rgba(0, 214, 255, 0.1)' }}
            >
              <div style={{ background: 'rgba(0, 214, 255, 0.1)', padding: '8px', borderRadius: '8px' }}><Download size={16} color="#00D6FF" /></div>
              <div style={{ flex: 1 }}>
                 <div style={{ fontWeight: 600, fontSize: '0.9375rem' }}>Export Data</div>
                 <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Download processed files</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
