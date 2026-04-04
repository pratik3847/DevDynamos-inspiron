import { useLocation } from 'react-router-dom';
import { CheckCircle2, FileUp, FileText, CheckSquare, Wrench, Download } from 'lucide-react';

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
    <div className="pipeline-tracker">
      <div className="pipeline-track">

        {STAGES.map((stage, idx) => {
          const isCompleted = idx < activeIndex;
          const isActive = idx === activeIndex;
          const stateClass = isCompleted ? 'is-complete' : isActive ? 'is-active' : '';
          const Icon = stage.icon;

          return (
            <div key={stage.id} className="pipeline-stage" aria-current={isActive ? 'step' : undefined}>
              <div className={`pipeline-node ${stateClass}`}>
                {isCompleted ? <CheckCircle2 size={20} /> : <Icon size={18} />}
              </div>
              <span className={`pipeline-label ${stateClass}`}>{stage.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
