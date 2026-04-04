import React from 'react';

interface ParsedJsonViewerProps {
  parsedJson: any;
}

export default function ParsedJsonViewer({ parsedJson }: ParsedJsonViewerProps) {
  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: '#fff' }}>Parsed Hierarchy</h3>
        <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Structure: JSON Tree</span>
      </div>
      
      <div style={{ 
        flex: 1, 
        background: 'rgba(0,0,0,0.4)', 
        borderRadius: '8px', 
        padding: '24px', 
        overflowY: 'auto',
        fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
        fontSize: '0.875rem',
        border: '1px solid rgba(255,255,255,0.05)'
      }}>
        {/* Simple recursive render for demo - ideally use a proper JSON tree component */}
        <pre style={{ margin: 0, color: 'var(--text-secondary)' }}>
          {JSON.stringify(parsedJson, null, 2).replace(/"([^"]+)":/g, '<span style="color: #00D6FF">"$1"</span>:')}
        </pre>
      </div>
    </div>
  );
}
