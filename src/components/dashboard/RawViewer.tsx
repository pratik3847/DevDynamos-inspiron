interface RawViewerProps {
  rawEdi: string;
}

export default function RawViewer({ rawEdi }: RawViewerProps) {
  const lines = rawEdi.split('~').filter(line => line.trim().length > 0);

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: '#fff' }}>Raw EDI Stream</h3>
        <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Format: X12</span>
      </div>
      
      <div style={{ 
        flex: 1, 
        background: 'rgba(0,0,0,0.4)', 
        borderRadius: '8px', 
        padding: '16px', 
        overflowY: 'auto',
        fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
        fontSize: '0.875rem',
        lineHeight: 1.6,
        border: '1px solid rgba(255,255,255,0.05)'
      }}>
        {lines.map((line, index) => {
          const segment = line.split('*')[0];
          let color = 'var(--text-primary)';
          if (['ISA', 'GS', 'ST', 'SE', 'GE', 'IEA'].includes(segment)) color = 'var(--accent-cyan)';
          if (['HL', 'NM1', 'CLM'].includes(segment)) color = 'var(--accent-blue)';

          return (
            <div key={index} style={{ display: 'flex', gap: '16px' }}>
              <div style={{ color: 'rgba(255,255,255,0.2)', width: '30px', textAlign: 'right', userSelect: 'none' }}>
                {index + 1}
              </div>
              <div style={{ flex: 1, wordBreak: 'break-all' }}>
                <span style={{ color, fontWeight: 600 }}>{segment}</span>
                <span style={{ color: 'var(--text-secondary)' }}>{line.substring(segment.length)}</span>
                <span style={{ color: 'rgba(255,255,255,0.2)' }}>~</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
