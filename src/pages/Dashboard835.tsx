import React, { useMemo, useState } from 'react';
import { AlertTriangle, ChevronDown, ChevronRight, Filter, Users } from 'lucide-react';
import { useSession } from '../context/SessionContext';
import { MemberEnrollmentSummaryMember } from '../services/types';

type MaintenanceMeta = {
  label: string;
  tone: string;
  bg: string;
  border: string;
};

type MemberRecord = {
  key: string;
  name: string;
  memberId: string;
  maintenanceCode: string;
  maintenanceMeta: MaintenanceMeta;
  relationshipCode: string;
  hasCob: boolean;
  dependents: MemberRecord[];
  familyGroup: string;
};

const MAINTENANCE_MAP: Record<string, MaintenanceMeta> = {
  '021': {
    label: '021 Addition',
    tone: '#1E8E3E',
    bg: 'rgba(30, 142, 62, 0.14)',
    border: 'rgba(30, 142, 62, 0.35)',
  },
  '024': {
    label: '024 Cancellation',
    tone: '#C5221F',
    bg: 'rgba(197, 34, 31, 0.14)',
    border: 'rgba(197, 34, 31, 0.35)',
  },
  '001': {
    label: '001 Change',
    tone: '#B36B00',
    bg: 'rgba(179, 107, 0, 0.14)',
    border: 'rgba(179, 107, 0, 0.35)',
  },
  '030': {
    label: '030 Audit',
    tone: '#5F6368',
    bg: 'rgba(95, 99, 104, 0.16)',
    border: 'rgba(95, 99, 104, 0.35)',
  },
};

const DEFAULT_MAINTENANCE: MaintenanceMeta = {
  label: 'Unknown',
  tone: 'var(--text-secondary)',
  bg: 'rgba(127, 127, 127, 0.12)',
  border: 'rgba(127, 127, 127, 0.3)',
};

function getElementValue(segment: any, position: number): string {
  const byPos = segment?.elements?.find((el: any) => String(el?.position) === String(position).padStart(2, '0'));
  if (byPos?.value != null) return String(byPos.value).trim();

  const byIndex = segment?.elements?.[position - 1];
  if (byIndex?.value != null) return String(byIndex.value).trim();

  return '';
}

function getMemberDisplayName(block: any[]): { name: string; memberId: string } {
  const nm1 = block.find((seg) => seg?.segmentId === 'NM1');
  const lastOrOrg = getElementValue(nm1, 3);
  const first = getElementValue(nm1, 4);
  const memberIdFromNm1 = getElementValue(nm1, 9);

  const name = [lastOrOrg, first].filter(Boolean).join(', ') || lastOrOrg || 'Unknown Member';

  const refMember = block.find((seg) => seg?.segmentId === 'REF' && getElementValue(seg, 1) === '0F');
  const memberIdFromRef = getElementValue(refMember, 2);

  return {
    name,
    memberId: memberIdFromRef || memberIdFromNm1 || '-',
  };
}

function parseMembersFromSegments(segments: any[]): MemberRecord[] {
  const blocks: any[][] = [];
  let current: any[] = [];

  for (const segment of segments) {
    if (segment?.segmentId === 'INS') {
      if (current.length > 0) blocks.push(current);
      current = [segment];
    } else if (current.length > 0) {
      current.push(segment);
    }
  }

  if (current.length > 0) blocks.push(current);

  const parsedMembers = blocks.map((block, index) => {
    const ins = block[0];
    const ins01 = getElementValue(ins, 1);
    const ins02 = getElementValue(ins, 2);
    const ins03 = getElementValue(ins, 3);

    const { name, memberId } = getMemberDisplayName(block);

    const hasCob = block.some((seg) => {
      const id = String(seg?.segmentId || '').toUpperCase();
      return id === 'COB' || id === 'OI' || id === 'SBR' || String(seg?.raw || '').includes('2320');
    });

    const maintenanceMeta = MAINTENANCE_MAP[ins03] || { ...DEFAULT_MAINTENANCE, label: ins03 ? `${ins03} Unknown` : 'Unknown' };

    return {
      key: `m_${index}_${memberId}`,
      name,
      memberId,
      maintenanceCode: ins03,
      maintenanceMeta,
      relationshipCode: ins02 || ins01,
      hasCob,
      dependents: [],
      familyGroup: '-',
    } as MemberRecord;
  });

  const families: MemberRecord[] = [];
  let currentSubscriber: MemberRecord | null = null;
  let familyCounter = 0;

  for (const member of parsedMembers) {
    const isSubscriber = member.relationshipCode === 'Y' || member.relationshipCode === '18' || member.relationshipCode === '01';

    if (isSubscriber || !currentSubscriber) {
      familyCounter += 1;
      member.familyGroup = `Family ${familyCounter}`;
      families.push(member);
      currentSubscriber = member;
    } else {
      member.familyGroup = currentSubscriber.familyGroup;
      currentSubscriber.dependents.push(member);
    }
  }

  return families;
}

function mapBackendSummaryFamilies(families: MemberEnrollmentSummaryMember[] | undefined): MemberRecord[] {
  if (!Array.isArray(families)) return [];

  const mapMember = (m: MemberEnrollmentSummaryMember): MemberRecord => {
    const maintenanceCode = String(m.maintenanceCode || '');
    const maintenanceMeta = MAINTENANCE_MAP[maintenanceCode]
      || { ...DEFAULT_MAINTENANCE, label: m.maintenanceLabel || (maintenanceCode ? `${maintenanceCode} Unknown` : 'Unknown') };

    return {
      key: m.key || `m_${m.memberId}_${m.name}`,
      name: m.name || 'Unknown Member',
      memberId: m.memberId || '-',
      maintenanceCode,
      maintenanceMeta,
      relationshipCode: m.relationshipCode || '',
      hasCob: !!m.hasCob,
      dependents: Array.isArray(m.dependents) ? m.dependents.map(mapMember) : [],
      familyGroup: m.familyGroup || '-',
    };
  };

  return families.map(mapMember);
}

export default function Dashboard835() {
  const { activeSession, isLoading } = useSession();
  const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});
  const [showCobOnly, setShowCobOnly] = useState(false);

  const families = useMemo(() => {
    const backendFamilies = mapBackendSummaryFamilies(activeSession?.memberEnrollmentSummary?.families);
    const parsed = backendFamilies.length > 0
      ? backendFamilies
      : parseMembersFromSegments(activeSession?.parsedJson?.segments || []);

    if (!showCobOnly) return parsed;

    return parsed
      .map((family) => ({
        ...family,
        dependents: family.dependents.filter((d) => d.hasCob),
      }))
      .filter((family) => family.hasCob || family.dependents.length > 0);
  }, [activeSession, showCobOnly]);

  const totalMembers = useMemo(
    () => families.reduce((acc, f) => acc + 1 + f.dependents.length, 0),
    [families]
  );

  const totalCob = useMemo(
    () => families.reduce((acc, f) => acc + (f.hasCob ? 1 : 0) + f.dependents.filter((d) => d.hasCob).length, 0),
    [families]
  );

  const toggleExpand = (key: string) => {
    setExpandedRows((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  if (!activeSession) {
    return (
      <div className="dash-card" style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <h2 style={{ marginBottom: '8px' }}>834 Dashboard</h2>
        <p style={{ color: 'var(--text-secondary)' }}>
          Upload/select a session first to render Member Enrollment Summary.
        </p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px', flexWrap: 'wrap' }}>
        <div>
          <h1 style={{ fontSize: '1.55rem', fontWeight: 700, marginBottom: '8px' }}>834 Dashboard</h1>
          <p style={{ color: 'var(--text-secondary)' }}>
            834 Feature: Member Enrollment Summary with maintenance-state badges, dependent rollup, and COB visibility.
          </p>
        </div>

        <div className="dash-card" style={{ padding: '12px 14px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Filter size={16} color="var(--text-secondary)" />
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={showCobOnly}
              onChange={(e) => setShowCobOnly(e.target.checked)}
              style={{ accentColor: '#f59e0b' }}
            />
            <span style={{ fontSize: '0.88rem', fontWeight: 600 }}>Show Only Members with COB</span>
          </label>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
        <div className="dash-card" style={{ padding: '16px' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Total Members</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 700 }}>{isLoading ? '...' : totalMembers}</div>
        </div>
        <div className="dash-card" style={{ padding: '16px' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Family Groups</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 700 }}>{isLoading ? '...' : families.length}</div>
        </div>
        <div className="dash-card" style={{ padding: '16px' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>COB Active</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 700, color: '#f59e0b' }}>{isLoading ? '...' : totalCob}</div>
        </div>
      </div>

      <div className="dash-card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '900px' }}>
            <thead>
              <tr style={{ background: 'rgba(255,255,255,0.04)' }}>
                <th style={{ textAlign: 'left', padding: '14px 16px', fontSize: '0.78rem', letterSpacing: '0.03em', color: 'var(--text-secondary)' }}>Member</th>
                <th style={{ textAlign: 'left', padding: '14px 16px', fontSize: '0.78rem', letterSpacing: '0.03em', color: 'var(--text-secondary)' }}>Member ID</th>
                <th style={{ textAlign: 'left', padding: '14px 16px', fontSize: '0.78rem', letterSpacing: '0.03em', color: 'var(--text-secondary)' }}>Maintenance Type</th>
                <th style={{ textAlign: 'left', padding: '14px 16px', fontSize: '0.78rem', letterSpacing: '0.03em', color: 'var(--text-secondary)' }}>Family Group</th>
                <th style={{ textAlign: 'left', padding: '14px 16px', fontSize: '0.78rem', letterSpacing: '0.03em', color: 'var(--text-secondary)' }}>Dependents</th>
                <th style={{ textAlign: 'left', padding: '14px 16px', fontSize: '0.78rem', letterSpacing: '0.03em', color: 'var(--text-secondary)' }}>COB View</th>
              </tr>
            </thead>
            <tbody>
              {!isLoading && families.length === 0 && (
                <tr>
                  <td colSpan={6} style={{ padding: '26px 16px', color: 'var(--text-secondary)', textAlign: 'center' }}>
                    No Loop 2000 INS member records found for the current session.
                  </td>
                </tr>
              )}

              {families.map((subscriber) => {
                const isExpanded = !!expandedRows[subscriber.key];
                const hasDependents = subscriber.dependents.length > 0;

                return (
                  <React.Fragment key={subscriber.key}>
                    <tr style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                      <td style={{ padding: '14px 16px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <button
                            type="button"
                            onClick={() => hasDependents && toggleExpand(subscriber.key)}
                            disabled={!hasDependents}
                            style={{
                              width: '24px',
                              height: '24px',
                              borderRadius: '6px',
                              border: '1px solid rgba(255,255,255,0.15)',
                              background: hasDependents ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.02)',
                              color: hasDependents ? 'var(--text-primary)' : 'var(--text-secondary)',
                              display: 'inline-flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              cursor: hasDependents ? 'pointer' : 'not-allowed',
                            }}
                            aria-label={hasDependents ? 'Toggle dependents' : 'No dependents'}
                          >
                            {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                          </button>

                          <span style={{ fontWeight: 700 }}>{subscriber.name}</span>

                          {subscriber.hasCob && (
                            <span
                              style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '4px',
                                color: '#f59e0b',
                                fontSize: '0.75rem',
                                fontWeight: 700,
                                border: '1px solid rgba(245, 158, 11, 0.35)',
                                background: 'rgba(245, 158, 11, 0.12)',
                                padding: '3px 8px',
                                borderRadius: '999px',
                              }}
                            >
                              <AlertTriangle size={12} /> COB Active
                            </span>
                          )}
                        </div>
                      </td>

                      <td style={{ padding: '14px 16px', fontFamily: 'monospace' }}>{subscriber.memberId}</td>

                      <td style={{ padding: '14px 16px' }}>
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            padding: '4px 10px',
                            borderRadius: '999px',
                            fontSize: '0.76rem',
                            fontWeight: 700,
                            color: subscriber.maintenanceMeta.tone,
                            background: subscriber.maintenanceMeta.bg,
                            border: `1px solid ${subscriber.maintenanceMeta.border}`,
                          }}
                        >
                          {subscriber.maintenanceMeta.label}
                        </span>
                      </td>

                      <td style={{ padding: '14px 16px' }}>{subscriber.familyGroup}</td>

                      <td style={{ padding: '14px 16px' }}>
                        {hasDependents ? (
                          <span style={{ color: '#00D6FF', fontWeight: 700 }}>+ {subscriber.dependents.length} Dependents</span>
                        ) : (
                          <span style={{ color: 'var(--text-secondary)' }}>No dependents</span>
                        )}
                      </td>

                      <td style={{ padding: '14px 16px' }}>
                        {subscriber.hasCob ? (
                          <span style={{ color: '#f59e0b', fontWeight: 700 }}>Active</span>
                        ) : (
                          <span style={{ color: 'var(--text-secondary)' }}>None</span>
                        )}
                      </td>
                    </tr>

                    {isExpanded &&
                      subscriber.dependents.map((dependent) => (
                        <tr key={dependent.key} style={{ background: 'rgba(0, 214, 255, 0.05)' }}>
                          <td style={{ padding: '12px 16px 12px 48px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <Users size={14} color="var(--text-secondary)" />
                              <span>{dependent.name}</span>
                              {dependent.hasCob && (
                                <span style={{ color: '#f59e0b', fontSize: '0.75rem', fontWeight: 700 }}>⚠ COB Active</span>
                              )}
                            </div>
                          </td>
                          <td style={{ padding: '12px 16px', fontFamily: 'monospace' }}>{dependent.memberId}</td>
                          <td style={{ padding: '12px 16px' }}>
                            <span
                              style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                padding: '4px 10px',
                                borderRadius: '999px',
                                fontSize: '0.76rem',
                                fontWeight: 700,
                                color: dependent.maintenanceMeta.tone,
                                background: dependent.maintenanceMeta.bg,
                                border: `1px solid ${dependent.maintenanceMeta.border}`,
                              }}
                            >
                              {dependent.maintenanceMeta.label}
                            </span>
                          </td>
                          <td style={{ padding: '12px 16px' }}>{dependent.familyGroup}</td>
                          <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>Dependent</td>
                          <td style={{ padding: '12px 16px' }}>{dependent.hasCob ? 'Active' : 'None'}</td>
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
