import React from 'react';
import { ValidationError } from '../../services/types';
import { AlertTriangle, AlertCircle, Info } from 'lucide-react';

interface ValidationPanelProps {
  errors: ValidationError[];
}

export default function ValidationPanel({ errors }: ValidationPanelProps) {
  if (errors.length === 0) {
    return (
      <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
        <div style={{ background: 'rgba(52, 199, 89, 0.1)', padding: '24px', borderRadius: '50%', marginBottom: '16px' }}>
          <AlertCircle size={48} color="#34C759" />
        </div>
        <h3 style={{ fontSize: '1.25rem', color: '#fff', marginBottom: '8px' }}>No Validation Errors</h3>
        <p>This file passes all SNIP rules and is ready for submission.</p>
      </div>
    );
  }

  return (
    <div style={{ height: '100%' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
         <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: '#fff' }}>Validation Report</h3>
         <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Found {errors.length} issue(s)</div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {errors.map(err => (
          <div key={err.id} className={`error-toast enhanced`} style={{ margin: 0, border: '1px solid rgba(255, 59, 48, 0.3)', opacity: 1, transform: 'none' }}>
            <div className="toast-header">
              <div className="icon-error" style={{ background: err.severity === 'Critical' ? 'var(--accent-red)' : '#FF9500' }}>
                {err.severity === 'Critical' ? <AlertCircle size={14} /> : <AlertTriangle size={14} />}
              </div>
              <span className="err-loc">Loop {err.loop} &rarr; Segment {err.segment} &rarr; {err.element}</span>
            </div>
            <div className="toast-body" style={{ color: '#fff', fontSize: '1rem' }}>
              {err.description}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.875rem', marginTop: '12px', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '12px' }}>
               <span style={{ color: 'var(--text-secondary)' }}>Rule: {err.rule}</span>
               <span className={`badge ${err.severity === 'Critical' ? 'outline text-red' : 'outline'}`} style={{ color: err.severity === 'Critical' ? '#FF3B30' : '#FF9500', margin: 0 }}>
                 {err.severity}
               </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
