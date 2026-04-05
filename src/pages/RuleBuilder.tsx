import { useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Database,
  Globe,
  RefreshCw,
  Save,
  Search,
  ShieldCheck,
  SlidersHorizontal,
} from 'lucide-react';
import { api } from '../services/api';
import { RuleCategory, RuleDefinition, RuleSeverity } from '../services/types';

const DEFAULT_RULES: RuleDefinition[] = [
  {
    id: 'ISA13-IEA02',
    name: 'Interchange control numbers match',
    category: 'Structural',
    severity: 'Critical',
    description: 'ISA13 must match IEA02 to validate interchange boundaries.',
    scope: ['837P', '835', '834'],
    source: 'HIPAA X12',
    tags: ['Envelope', 'Control'],
    enabled: true,
    defaultEnabled: true,
    runtime: 'Realtime',
    lastUpdated: '2026-03-28',
  },
  {
    id: 'GS06-GE02',
    name: 'Functional group control alignment',
    category: 'Structural',
    severity: 'Error',
    description: 'GS06 must match GE02 to keep group counts aligned.',
    scope: ['837P', '835', '834'],
    source: 'HIPAA X12',
    tags: ['Group', 'Control'],
    enabled: true,
    defaultEnabled: true,
    runtime: 'Realtime',
    lastUpdated: '2026-03-29',
  },
  {
    id: 'SE01-SEGCOUNT',
    name: 'Segment count validation',
    category: 'Structural',
    severity: 'Error',
    description: 'SE01 must equal the number of segments from ST to SE.',
    scope: ['837P', '835', '834'],
    source: 'HIPAA X12',
    tags: ['Trailer', 'Count'],
    enabled: true,
    defaultEnabled: true,
    runtime: 'Realtime',
    lastUpdated: '2026-03-28',
  },
  {
    id: 'NM1-85-REQUIRED',
    name: 'Billing provider required',
    category: 'Business',
    severity: 'Critical',
    description: 'NM1 segment with entity code 85 is required for all claims.',
    scope: ['837P'],
    source: 'TR3 837P',
    tags: ['Provider', 'Required'],
    enabled: true,
    defaultEnabled: true,
    runtime: 'Realtime',
    lastUpdated: '2026-03-27',
  },
  {
    id: 'CLM-PRIORITY',
    name: 'Claim filing indicator check',
    category: 'Business',
    severity: 'Warning',
    description: 'CLM05-3 must be present when other payer info exists.',
    scope: ['837P'],
    source: 'TR3 837P',
    tags: ['Claim', 'Coordination'],
    enabled: true,
    defaultEnabled: true,
    runtime: 'Realtime',
    lastUpdated: '2026-03-24',
  },
  {
    id: 'REF-EI-REQUIRED',
    name: 'Employer ID required for 834',
    category: 'Business',
    severity: 'Error',
    description: 'REF segment with qualifier EI must be present for sponsor.',
    scope: ['834'],
    source: 'TR3 834',
    tags: ['Sponsor', 'Enrollment'],
    enabled: true,
    defaultEnabled: true,
    runtime: 'Realtime',
    lastUpdated: '2026-03-18',
  },
  {
    id: 'DTM-ESRD',
    name: 'ESRD date format enforcement',
    category: 'Business',
    severity: 'Warning',
    description: 'DTM segment must follow CCYYMMDD format for ESRD dates.',
    scope: ['837P', '834'],
    source: 'Internal Policy',
    tags: ['Dates', 'Format'],
    enabled: true,
    defaultEnabled: true,
    runtime: 'Realtime',
    lastUpdated: '2026-03-16',
  },
  {
    id: 'NPI-ACTIVE',
    name: 'Provider NPI active in NPPES',
    category: 'External',
    severity: 'Error',
    description: 'NPI must resolve to an active provider record in NPPES.',
    scope: ['837P', '835'],
    source: 'NPPES',
    tags: ['Provider', 'NPI'],
    enabled: true,
    defaultEnabled: true,
    runtime: 'External',
    lastUpdated: '2026-03-22',
  },
  {
    id: 'CODESET-ICD10',
    name: 'ICD-10 diagnosis code validation',
    category: 'External',
    severity: 'Error',
    description: 'Diagnosis codes must exist in the ICD-10 CM code set.',
    scope: ['837P'],
    source: 'CMS Code Sets',
    tags: ['Codes', 'Clinical'],
    enabled: true,
    defaultEnabled: true,
    runtime: 'External',
    lastUpdated: '2026-03-20',
  },
  {
    id: 'CODESET-HCPCS',
    name: 'HCPCS service code validation',
    category: 'External',
    severity: 'Warning',
    description: 'HCPCS service codes must be active for the service date.',
    scope: ['837P'],
    source: 'CMS Code Sets',
    tags: ['Codes', 'Services'],
    enabled: false,
    defaultEnabled: false,
    runtime: 'External',
    lastUpdated: '2026-03-15',
  },
  {
    id: 'BPR02-AMOUNT',
    name: 'Payment amount precision check',
    category: 'Business',
    severity: 'Info',
    description: 'BPR02 must contain a valid monetary amount with 2 decimals.',
    scope: ['835'],
    source: 'TR3 835',
    tags: ['Payment', 'Amount'],
    enabled: true,
    defaultEnabled: true,
    runtime: 'Realtime',
    lastUpdated: '2026-03-10',
  },
];

const withDelay = (value: string) => ({ ['--delay' as any]: value });

export default function RuleBuilder() {
  const [rules, setRules] = useState<RuleDefinition[]>([]);
  const [savedRules, setSavedRules] = useState<RuleDefinition[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<'all' | RuleCategory>('all');
  const [severityFilter, setSeverityFilter] = useState<'all' | RuleSeverity>('all');
  const [statusFilter, setStatusFilter] = useState<'all' | 'enabled' | 'disabled'>('all');
  const [scopeFilter, setScopeFilter] = useState<'all' | '837P' | '835' | '834'>('all');
  const [lastSavedAt, setLastSavedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      setLoading(true);
      try {
        const data = await api.getRules();
        if (!mounted) return;
        const incoming = data.rules.length > 0 ? data.rules : DEFAULT_RULES;
        setRules(incoming);
        setSavedRules(incoming);
        setLastSavedAt(data.updatedAt || null);
        setLoadError(null);
      } catch (err) {
        if (!mounted) return;
        const message = err instanceof Error ? err.message : 'Unable to load rule preferences.';
        setLoadError(message);
        setRules(DEFAULT_RULES);
        setSavedRules(DEFAULT_RULES);
      } finally {
        if (mounted) setLoading(false);
      }
    };

    load();
    return () => {
      mounted = false;
    };
  }, []);

  const toggleRule = (ruleId: string) => {
    setRules((prev) =>
      prev.map((rule) => (rule.id === ruleId ? { ...rule, enabled: !rule.enabled } : rule))
    );
  };

  const resetDefaults = async () => {
    setSaving(true);
    try {
      const data = await api.resetRules();
      const incoming = data.rules.length > 0 ? data.rules : DEFAULT_RULES;
      setRules(incoming);
      setSavedRules(incoming);
      setLastSavedAt(data.updatedAt || null);
      setLoadError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unable to reset rules.';
      setLoadError(message);
      setRules(DEFAULT_RULES);
      setSavedRules(DEFAULT_RULES);
    } finally {
      setSaving(false);
    }
  };

  const saveChanges = async () => {
    setSaving(true);
    try {
      const data = await api.updateRules(rules);
      const incoming = data.rules.length > 0 ? data.rules : rules;
      setRules(incoming);
      setSavedRules(incoming);
      setLastSavedAt(data.updatedAt || new Date().toISOString());
      setLoadError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unable to save rules.';
      setLoadError(message);
    } finally {
      setSaving(false);
    }
  };

  const clearFilters = () => {
    setSearchTerm('');
    setCategoryFilter('all');
    setSeverityFilter('all');
    setStatusFilter('all');
    setScopeFilter('all');
  };

  const pendingCount = useMemo(() => {
    const savedMap = new Map(savedRules.map((rule) => [rule.id, rule.enabled]));
    return rules.reduce((count, rule) => {
      const saved = savedMap.get(rule.id);
      if (typeof saved === 'boolean' && saved !== rule.enabled) return count + 1;
      return count;
    }, 0);
  }, [rules, savedRules]);

  const enabledCount = useMemo(() => rules.filter((rule) => rule.enabled).length, [rules]);
  const disabledCount = rules.length - enabledCount;

  const categoryStats = useMemo(() => {
    return ['Structural', 'Business', 'External'].map((category) => {
      const total = rules.filter((rule) => rule.category === category).length;
      const enabled = rules.filter((rule) => rule.category === category && rule.enabled).length;
      return {
        category,
        total,
        enabled,
      };
    });
  }, [rules]);

  const filteredRules = useMemo(() => {
    const term = searchTerm.trim().toLowerCase();
    return rules.filter((rule) => {
      if (categoryFilter !== 'all' && rule.category !== categoryFilter) return false;
      if (severityFilter !== 'all' && rule.severity !== severityFilter) return false;
      if (statusFilter === 'enabled' && !rule.enabled) return false;
      if (statusFilter === 'disabled' && rule.enabled) return false;
      if (scopeFilter !== 'all' && !rule.scope.includes(scopeFilter)) return false;
      if (!term) return true;
      const haystack = [
        rule.id,
        rule.name,
        rule.description,
        rule.source,
        rule.tags.join(' '),
      ]
        .join(' ')
        .toLowerCase();
      return haystack.includes(term);
    });
  }, [rules, searchTerm, categoryFilter, severityFilter, statusFilter, scopeFilter]);

  const statusLabel = loading
    ? 'Loading rules'
    : pendingCount > 0
      ? `${pendingCount} change(s) pending`
      : 'All changes saved';
  const statusTone = loading ? 'muted' : pendingCount > 0 ? 'is-pending' : 'is-saved';
  const savedLabel = lastSavedAt ? new Date(lastSavedAt).toLocaleString() : 'Not saved yet';
  const syncLabel = loadError ? 'Sync unavailable' : 'Saved to account';

  return (
    <div className="edi-page rules-page">
      <div className="edi-page__header rules-hero dash-card" style={withDelay('0ms')}>
        <div className="rules-hero__copy">
          <div className="rules-eyebrow">Rule Registry</div>
          <h1 className="rules-title">Rule Builder</h1>
          <p className="rules-subtitle">
            Enable or disable validation rules across structural, business, and external checks.
          </p>
          <div className="rules-hero__meta">
            <span className={`rules-status-pill ${statusTone}`}>
              <CheckCircle2 size={14} /> {statusLabel}
            </span>
            <span className="rules-status-pill muted">Last saved: {savedLabel}</span>
            <span className="rules-status-pill muted">{syncLabel}</span>
          </div>
        </div>
        <div className="rules-hero__actions">
          <button type="button" className="btn outline" onClick={resetDefaults} disabled={loading || saving}>
            <RefreshCw size={16} /> Reset defaults
          </button>
          <button
            type="button"
            className="btn primary"
            onClick={saveChanges}
            disabled={pendingCount === 0 || loading || saving}
          >
            <Save size={16} /> Save preferences
          </button>
        </div>
      </div>

      <div className="edi-grid edi-grid--4 rules-overview">
        {[
          { label: 'Total Rules', value: rules.length },
          { label: 'Enabled Rules', value: enabledCount },
          { label: 'External Checks', value: rules.filter((rule) => rule.category === 'External' && rule.enabled).length },
          { label: 'Pending Changes', value: pendingCount },
        ].map((item, index) => (
          <div key={item.label} className="dash-card rules-metric" style={withDelay(`${index * 80}ms`)}>
            <div className="rules-metric__label">{item.label}</div>
            <div className="rules-metric__value">{item.value}</div>
          </div>
        ))}
      </div>

      <div className="dash-card rules-toolbar" style={withDelay('120ms')}>
        <div className="rules-toolbar__header">
          <div>
            <div className="rules-toolbar__title">
              <SlidersHorizontal size={18} /> Filter rules
            </div>
            <div className="rules-toolbar__subtitle">Target the rules you want to manage right now.</div>
          </div>
          <button type="button" className="btn outline" onClick={clearFilters}>
            Clear filters
          </button>
        </div>

        <div className="rules-toolbar__filters">
          <label className="rules-input">
            <Search size={16} />
            <input
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search by rule id, tag, or segment"
            />
          </label>

          <label className="rules-select">
            <span>Category</span>
            <select value={categoryFilter} onChange={(event) => setCategoryFilter(event.target.value as any)}>
              <option value="all">All categories</option>
              <option value="Structural">Structural</option>
              <option value="Business">Business</option>
              <option value="External">External</option>
            </select>
          </label>

          <label className="rules-select">
            <span>Severity</span>
            <select value={severityFilter} onChange={(event) => setSeverityFilter(event.target.value as any)}>
              <option value="all">All severities</option>
              <option value="Critical">Critical</option>
              <option value="Error">Error</option>
              <option value="Warning">Warning</option>
              <option value="Info">Info</option>
            </select>
          </label>

          <label className="rules-select">
            <span>Status</span>
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as any)}>
              <option value="all">All</option>
              <option value="enabled">Enabled</option>
              <option value="disabled">Disabled</option>
            </select>
          </label>

          <label className="rules-select">
            <span>Transaction</span>
            <select value={scopeFilter} onChange={(event) => setScopeFilter(event.target.value as any)}>
              <option value="all">All</option>
              <option value="837P">837P</option>
              <option value="835">835</option>
              <option value="834">834</option>
            </select>
          </label>
        </div>
      </div>

      <div className="edi-grid edi-grid--3 rules-category-grid">
        {categoryStats.map((item, index) => (
          <div
            key={item.category}
            className="dash-card rules-category"
            data-category={item.category}
            style={withDelay(`${index * 100 + 120}ms`)}
          >
            <div className="rules-category__header">
              <div className="rules-category__icon">
                {item.category === 'Structural' && <ShieldCheck size={18} />}
                {item.category === 'Business' && <AlertTriangle size={18} />}
                {item.category === 'External' && <Globe size={18} />}
              </div>
              <div>
                <div className="rules-category__name">{item.category}</div>
                <div className="rules-category__sub">{item.enabled} of {item.total} enabled</div>
              </div>
            </div>
            <div className="rules-category__bar">
              <div
                className="rules-category__fill"
                style={{ width: item.total === 0 ? '0%' : `${Math.round((item.enabled / item.total) * 100)}%` }}
              ></div>
            </div>
          </div>
        ))}
      </div>

      <div className="rules-grid">
        {loading ? (
          <div className="dash-card rules-empty">
            <AlertCircle size={36} />
            <div>
              <div className="rules-empty__title">Loading rules</div>
              <div className="rules-empty__subtitle">Fetching your saved preferences.</div>
            </div>
          </div>
        ) : filteredRules.length === 0 ? (
          <div className="dash-card rules-empty">
            <AlertCircle size={36} />
            <div>
              <div className="rules-empty__title">No matching rules</div>
              <div className="rules-empty__subtitle">Try adjusting your filters or search query.</div>
            </div>
          </div>
        ) : (
          filteredRules.map((rule, index) => (
            <div
              key={rule.id}
              className="dash-card rule-card"
              data-category={rule.category}
              data-severity={rule.severity}
              style={withDelay(`${index * 40}ms`)}
            >
              <div className="rule-card__header">
                <div className="rule-card__title">
                  <div className="rule-card__icon">
                    {rule.category === 'Structural' && <ShieldCheck size={18} />}
                    {rule.category === 'Business' && <Database size={18} />}
                    {rule.category === 'External' && <Globe size={18} />}
                  </div>
                  <div>
                    <div className="rule-card__name">{rule.name}</div>
                    <div className="rule-card__id">{rule.id}</div>
                  </div>
                </div>
                <label className="rule-toggle">
                  <input
                    type="checkbox"
                    checked={rule.enabled}
                    onChange={() => toggleRule(rule.id)}
                    aria-label={`Toggle ${rule.name}`}
                  />
                  <span className="rule-toggle__track">
                    <span className="rule-toggle__thumb" />
                  </span>
                  <span className="rule-toggle__label">{rule.enabled ? 'Enabled' : 'Disabled'}</span>
                </label>
              </div>

              <p className="rule-card__description">{rule.description}</p>

              <div className="rule-card__meta">
                <span className="rule-chip" data-category={rule.category}>
                  {rule.category}
                </span>
                <span className="rule-chip" data-severity={rule.severity}>
                  {rule.severity}
                </span>
                <span className="rule-chip is-neutral">{rule.runtime}</span>
              </div>

              <div className="rule-card__footer">
                <div className="rule-card__scope">Scope: {rule.scope.join(', ')}</div>
                <div className="rule-card__source">Source: {rule.source}</div>
                <div className="rule-card__tags">
                  {rule.tags.slice(0, 3).map((tag) => (
                    <span key={tag} className="rule-tag">{tag}</span>
                  ))}
                </div>
              </div>

              <div className="rule-card__updated">Last updated: {rule.lastUpdated}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
