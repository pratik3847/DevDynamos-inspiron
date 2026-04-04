import React from 'react';
import { useLocation } from 'react-router-dom';
import { CheckCircle2, ChevronRight, FileUp, FileText, CheckSquare, Wrench, Download } from 'lucide-react';

const STAGES = [
  { id: 'upload', label: 'Upload', icon: FileUp, path: '/dashboard/upload' },
  { id: 'parse', label: 'Parse', icon: FileText, path: '/dashboard/parser' },
  { id: 'validate', label: 'Validate', icon: CheckSquare, path: '/dashboard/validation' },
  { id: 'fix', label: 'Fix', icon: Wrench, path: '/dashboard/fix-assistant' },
  { id: 'export', label: 'Export', icon: Download, path: '/dashboard/export' }, // Mocking export since it's the last stage
];

export default function PipelineTracker() {
  const location = useLocation();
  const currentPath = location.pathname;

  // Determine current active index based on route mapping
  let activeIndex = -1;
  STAGES.forEach((stage, idx) => {
    if (currentPath.includes(stage.path)) {
      activeIndex = idx;
    }
  });

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 1, margin: '0 40px' }}>
      <div style={{ display: 'flex', alignItems: 'center', width: '100%', maxWidth: '800px', justifyContent: 'space-between', position: 'relative' }}>
        
        {/* Background connector line */}
        <div style={{ position: 'absolute', top: '24px', left: '10%', right: '10%', height: '2px', background: 'rgba(255,255,255,0.1)', zIndex: 0 }}></div>
        
        {STAGES.map((stage, idx) => {
          const isCompleted = idx < activeIndex;
          const isActive = idx === activeIndex;
          
          return (
            <div key={stage.id} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', zIndex: 1, position: 'relative' }}>
              <div style={{ 
                width: '48px', 
                height: '48px', 
                borderRadius: '50%', 
                background: isActive ? 'rgba(0, 80, 255, 0.1)' : 'var(--bg-card)', 
                border: `1px solid ${isActive ? '#0050FF' : isCompleted ? '#34C759' : 'rgba(255,255,255,0.1)'}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: isActive ? '#0050FF' : isCompleted ? '#34C759' : 'var(--text-secondary)',
                boxShadow: isActive ? '0 0 20px rgba(0, 80, 255, 0.2)' : 'none',
                transition: 'all 0.3s ease'
              }}>
                {isCompleted ? <CheckCircle2 size={24} /> : <stage.icon size={20} />}
              </div>
              <span style={{ fontSize: '0.75rem', fontWeight: isActive ? 600 : 500, color: isActive ? '#fff' : 'var(--text-secondary)' }}>
                {stage.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
