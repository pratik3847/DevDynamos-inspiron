import { useEffect, useRef, useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { 
  LayoutDashboard, FileUp, FileText, CheckSquare, Wrench, 
  BarChart, Activity, Settings, Sun, Moon, ChevronLeft, ChevronRight, LogOut
} from 'lucide-react';
import PipelineTracker from './PipelineTracker';
import EddieAssistant from './EddieAssistant';
import './DashboardLayout.css'; 

export default function DashboardLayout() {
  const { user, logoutState } = useAuth();
  const navigate = useNavigate();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    const storedTheme = localStorage.getItem('dashboard_theme');
    return storedTheme === 'light' ? 'light' : 'dark';
  });
  const profileMenuRef = useRef<HTMLDivElement>(null);
  const profileButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    localStorage.setItem('dashboard_theme', theme);
  }, [theme]);

  useEffect(() => {
    const handleClick = (event: MouseEvent) => {
      const target = event.target as Node;
      if (
        profileMenuRef.current &&
        profileButtonRef.current &&
        !profileMenuRef.current.contains(target) &&
        !profileButtonRef.current.contains(target)
      ) {
        setIsProfileOpen(false);
      }
    };

    if (isProfileOpen) {
      document.addEventListener('mousedown', handleClick);
    }

    return () => {
      document.removeEventListener('mousedown', handleClick);
    };
  }, [isProfileOpen]);

  return (
    <div className={`dashboard-container theme-${theme}`} style={{ minHeight: '100vh', display: 'flex' }}>
      
      {/* Sidebar navigation */}
      <div className={`dashboard-sidebar ${isSidebarCollapsed ? 'collapsed' : ''}`} style={{ width: isSidebarCollapsed ? '72px' : '260px', display: 'flex', flexDirection: 'column' }}>
        <div className="dashboard-brand" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}>
          <div style={{ width: '32px', height: '32px', background: 'var(--accent-blue)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Activity size={18} color="#fff" />
          </div>
          <span className="brand-text" style={{ fontWeight: 700, fontSize: '1.25rem' }} onClick={() => navigate('/')}>EDI Flow</span>
          <button
            type="button"
            className="sidebar-collapse"
            onClick={() => setIsSidebarCollapsed((prev) => !prev)}
            aria-label={isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isSidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>

        <div className="sidebar-scroll">
          <div className="nav-group-label" style={{ padding: '24px 24px 8px', fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>Core Pipeline</div>
          <nav className="dashboard-nav" style={{ padding: '0 12px' }}>
            <NavLink to="/dashboard" end className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} title="Dashboard">
              <LayoutDashboard size={18} /> <span className="nav-label">Dashboard</span>
            </NavLink>
            <NavLink to="/dashboard/upload" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} title="Upload">
              <FileUp size={18} /> <span className="nav-label">Upload</span>
            </NavLink>
            <NavLink to="/dashboard/parser" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} title="Parser">
              <FileText size={18} /> <span className="nav-label">Parser</span>
            </NavLink>
            <NavLink to="/dashboard/validation" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} title="Validation">
              <CheckSquare size={18} /> <span className="nav-label">Validation</span>
            </NavLink>
            <NavLink to="/dashboard/fix-assistant" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} title="Fix Assistant">
              <Wrench size={18} /> <span className="nav-label">Fix Assistant</span>
            </NavLink>
          </nav>

          <div className="nav-group-label" style={{ padding: '24px 24px 8px', fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>Analytics & Tools</div>
          <nav className="dashboard-nav" style={{ padding: '0 12px' }}>
            <NavLink to="/dashboard/835" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} title="834 Dashboard">
              <BarChart size={18} /> <span className="nav-label">834 Dashboard</span>
            </NavLink>
            <NavLink to="/dashboard/834" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} title="835 Dashboard">
              <BarChart size={18} /> <span className="nav-label">835 Dashboard</span>
            </NavLink>
            <NavLink to="/dashboard/rules" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} title="Rule Builder">
              <Settings size={18} /> <span className="nav-label">Rule Builder</span>
            </NavLink>
          </nav>
        </div>

        <div className="sidebar-profile" style={{ marginTop: 'auto', padding: '16px' }}>
          <div className="profile-summary">
            <div className="profile-avatar">
              {user?.name?.charAt(0).toUpperCase() || 'A'}
            </div>
            <div className="profile-meta" style={{ flex: 1, overflow: 'hidden' }}>
              <div style={{ fontWeight: 600, fontSize: '0.875rem', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>{user?.name || 'Admin User'}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>{user?.email || 'admin@ediflow.com'}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="dashboard-main" style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
        
        {/* Top Header */}
        <header className="dashboard-header">
          <PipelineTracker />

          <div className="dashboard-actions">
            <button
              type="button"
              className="theme-toggle"
              onClick={() => setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))}
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <div className="profile-menu-wrapper">
              <button
                ref={profileButtonRef}
                type="button"
                className="profile-trigger"
                onClick={() => setIsProfileOpen((prev) => !prev)}
                aria-label="Open profile menu"
              >
                <span className="profile-trigger-avatar">
                  {user?.name?.charAt(0).toUpperCase() || 'A'}
                </span>
              </button>
              {isProfileOpen && (
                <div ref={profileMenuRef} className="profile-menu header-menu">
                  <div className="profile-menu-header">
                    <div className="profile-menu-avatar">
                      {user?.name?.charAt(0).toUpperCase() || 'A'}
                    </div>
                    <div>
                      <div className="profile-menu-name">{user?.name || 'Admin User'}</div>
                      <div className="profile-menu-email">{user?.email || 'admin@ediflow.com'}</div>
                    </div>
                  </div>
                  <button type="button" className="profile-menu-item" onClick={logoutState}>
                    <LogOut size={16} /> Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Page Content Scroll */}
        <div className="dashboard-content">
          <Outlet />
        </div>

        <EddieAssistant theme={theme} />
      </div>
    </div>
  );
}
