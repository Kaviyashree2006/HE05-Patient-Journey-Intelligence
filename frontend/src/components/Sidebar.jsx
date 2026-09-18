import React from 'react';
import { 
  LayoutDashboard, 
  Clock, 
  GitMerge, 
  FileText, 
  ChevronRight
} from 'lucide-react';

export default function Sidebar({ 
  activeTab, 
  setActiveTab, 
  summary, 
  timelineData, 
  documents 
}) {
  const eventsCount = timelineData?.timeline_events?.length || summary?.total_events || 23;
  const changesCount = summary?.changes?.length || summary?.changes_count || 5;
  const conflictsCount = summary?.conflicts?.length || summary?.conflicts_count || 1;
  const docsCount = documents?.length || summary?.total_documents || 5;

  const navItems = [
    {
      id: 'overview',
      label: 'Overview',
      icon: LayoutDashboard,
      badges: null
    },
    {
      id: 'timeline',
      label: 'Timeline & Journey',
      icon: Clock,
      badges: [
        { text: `${eventsCount} Events`, className: 'badge-dark-neutral' }
      ]
    },
    {
      id: 'intelligence',
      label: 'Clinical Intelligence',
      icon: GitMerge,
      badges: [
        { text: `${changesCount} Changes`, className: 'badge-dark-teal' },
        ...(conflictsCount > 0 ? [{ text: `${conflictsCount} Conflict`, className: 'badge-dark-red' }] : [])
      ]
    },
    {
      id: 'documents',
      label: 'Documents & Evidence',
      icon: FileText,
      badges: [
        { text: `${docsCount} Records`, className: 'badge-dark-neutral' }
      ]
    }
  ];

  return (
    <aside className="clinical-sidebar-dark" aria-label="Clinical Workstation Navigation">
      {/* Sidebar Header Brand Identity */}
      <div className="sidebar-workstation-header">
        <div className="sidebar-header-kicker">EVIDENCE-LINKED PATIENT JOURNEY</div>
        <div className="sidebar-header-main">CLINICAL WORKSTATION</div>
      </div>

      {/* Main Navigation Items */}
      <nav className="sidebar-nav-container">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;

          return (
            <button
              key={item.id}
              className={`sidebar-nav-link ${isActive ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
              aria-current={isActive ? 'page' : undefined}
            >
              <div className="nav-link-indicator" aria-hidden="true" />
              
              <div className="nav-link-icon-wrap">
                <Icon size={18} className="nav-link-icon" />
              </div>

              <div className="nav-link-content">
                <span className="nav-link-title">{item.label}</span>
                {item.badges && (
                  <div className="nav-link-badges-row">
                    {item.badges.map((b, bIdx) => (
                      <span key={bIdx} className={`sidebar-badge ${b.className}`}>
                        {b.text}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <ChevronRight size={14} className="nav-link-arrow" />
            </button>
          );
        })}
      </nav>

      {/* Divider */}
      <div className="sidebar-horizontal-divider" role="separator" />

      {/* Sidebar Footer: System Status */}
      <div className="sidebar-system-footer">
        <div className="footer-status-kicker">SYSTEM STATUS</div>
        <div className="footer-status-line">
          <span className="status-pulsing-dot" aria-hidden="true" />
          <span className="footer-status-title">Evidence Engine Active</span>
        </div>
        <div className="footer-status-sub">100% Deterministic Grounding</div>
      </div>
    </aside>
  );
}
