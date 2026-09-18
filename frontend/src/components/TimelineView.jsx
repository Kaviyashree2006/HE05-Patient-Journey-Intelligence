import React, { useState, useMemo } from 'react';
import { 
  Clock, 
  Search, 
  ExternalLink, 
  FileText, 
  Activity,
  Pill,
  Stethoscope,
  Scan,
  LogOut,
  ChevronRight,
  ShieldCheck,
  Calendar,
  Network,
  GitBranch,
  Flag,
  ArrowDown,
  ArrowRight,
  AlertCircle
} from 'lucide-react';
import PatientJourneyGraph from './PatientJourneyGraph';

export default function TimelineView({ 
  timelineData, 
  summary,
  patientId,
  onSelectEvent, 
  onInspectDocument 
}) {
  const [subView, setSubView] = useState('timeline'); // 'timeline', 'chains', 'graph'
  const [eventTypeFilter, setEventTypeFilter] = useState('all');
  const [priorityFilter, setPriorityFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  const events = timelineData?.timeline_events || [];
  const gaps = summary?.gaps || [];
  const milestones = summary?.milestones || [];
  const chains = summary?.chains || [];

  // Filter events locally
  const filteredEvents = useMemo(() => {
    return events.filter((ev) => {
      if (eventTypeFilter !== 'all' && ev.event_type !== eventTypeFilter) return false;
      if (priorityFilter !== 'all' && (ev.importance_priority || 'Moderate') !== priorityFilter) return false;
      if (searchTerm) {
        const q = searchTerm.toLowerCase();
        const matchDesc = ev.event_description?.toLowerCase().includes(q);
        const matchSupp = ev.supporting_text?.toLowerCase().includes(q);
        const matchDoc = ev.source_document_name?.toLowerCase().includes(q);
        if (!matchDesc && !matchSupp && !matchDoc) return false;
      }
      return true;
    });
  }, [events, eventTypeFilter, priorityFilter, searchTerm]);

  // Merge events, inline documentation gaps, and milestone markers along the chronological spine
  const timelineStream = useMemo(() => {
    const items = [];
    const handledGaps = new Set();

    // Map milestones by date
    const milestoneMap = new Map();
    milestones.forEach((m) => {
      if (m.milestone_date) {
        if (!milestoneMap.has(m.milestone_date)) {
          milestoneMap.set(m.milestone_date, []);
        }
        milestoneMap.get(m.milestone_date).push(m);
      }
    });

    filteredEvents.forEach((ev, idx) => {
      items.push({ type: 'event', data: ev });

      // Check if a documentation gap starts on/after this event and precedes the next
      const nextEv = filteredEvents[idx + 1];
      if (nextEv) {
        gaps.forEach((g) => {
          if (!handledGaps.has(g.gap_id)) {
            if (ev.event_date <= g.gap_start_date && nextEv.event_date >= g.gap_end_date) {
              items.push({ type: 'gap', data: g });
              handledGaps.add(g.gap_id);
            }
          }
        });
      }
    });

    // Append any unhandled gaps
    gaps.forEach((g) => {
      if (!handledGaps.has(g.gap_id)) {
        items.push({ type: 'gap', data: g });
        handledGaps.add(g.gap_id);
      }
    });

    return { items, milestoneMap };
  }, [filteredEvents, gaps, milestones]);

  // Semantic category colors & icons
  // LAB → blue, MEDICATION → teal, IMAGING → purple, CLINICAL NOTE → slate, DISCHARGE → indigo, GAP → amber
  const getEventCategoryMeta = (type) => {
    switch (type) {
      case 'test':
        return { label: 'LAB', colorClass: 'cat-lab', icon: Activity };
      case 'medication':
        return { label: 'MEDICATION', colorClass: 'cat-med', icon: Pill };
      case 'condition':
        return { label: 'CLINICAL NOTE', colorClass: 'cat-note', icon: Stethoscope };
      case 'procedure':
        return { label: 'IMAGING', colorClass: 'cat-imaging', icon: Scan };
      case 'discharge':
        return { label: 'DISCHARGE', colorClass: 'cat-discharge', icon: LogOut };
      default:
        return { label: 'CLINICAL', colorClass: 'cat-slate', icon: Clock };
    }
  };

  const getPriorityIndicator = (priority) => {
    switch (priority) {
      case 'Critical':
        return <span className="priority-dot priority-critical" title="Priority: Critical">● Critical</span>;
      case 'High':
        return <span className="priority-dot priority-high" title="Priority: High">● High</span>;
      case 'Moderate':
        return <span className="priority-dot priority-moderate" title="Priority: Moderate">● Moderate</span>;
      default:
        return <span className="priority-dot priority-info" title="Priority: Informational">○ Info</span>;
    }
  };

  return (
    <div className="clinical-timeline-page animate-fade-in">
      {/* 1. HERO PAGE HEADER */}
      <div className="timeline-hero-header">
        <div className="timeline-hero-left">
          <div className="hero-title-row">
            <h1 className="timeline-page-title">TIMELINE & JOURNEY</h1>
            <span className="hero-event-count-badge font-mono">{events.length} Events</span>
            <span className="hero-period-label">Jan → Aug 2026</span>
          </div>
          <p className="timeline-page-sub">
            Continuous evidence-linked clinical chronology with milestone chapters, medication titrations, and inline documentation gap analysis.
          </p>
        </div>

        {/* Sub-View Switcher Tabs */}
        <div className="timeline-mode-switcher">
          <button 
            type="button"
            className={`mode-switch-btn ${subView === 'timeline' ? 'active' : ''}`}
            onClick={() => setSubView('timeline')}
          >
            <Clock size={14} />
            <span>Chronological Timeline</span>
          </button>

          <button 
            type="button"
            className={`mode-switch-btn ${subView === 'chains' ? 'active' : ''}`}
            onClick={() => setSubView('chains')}
          >
            <Network size={14} />
            <span>Action Chains</span>
            <span className="count-pill">{chains.length}</span>
          </button>

          <button 
            type="button"
            className={`mode-switch-btn ${subView === 'graph' ? 'active' : ''}`}
            onClick={() => setSubView('graph')}
          >
            <GitBranch size={14} />
            <span>Journey Graph</span>
          </button>
        </div>
      </div>

      {/* SUBVIEW 1: CHRONOLOGICAL CLINICAL SPINE */}
      {subView === 'timeline' && (
        <div className="chronological-spine-view">
          {/* Compact Filter Strip (Non-intrusive) */}
          <div className="compact-timeline-filter-strip">
            <div className="filter-search-wrap">
              <Search size={14} className="filter-search-icon" />
              <input 
                type="text"
                placeholder="Filter events, labs, medications, findings..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="filter-search-input"
              />
              {searchTerm && (
                <button type="button" className="filter-clear-btn" onClick={() => setSearchTerm('')}>Clear</button>
              )}
            </div>

            <div className="filter-button-cluster">
              <div className="filter-cluster-group">
                <span className="cluster-label">Type:</span>
                {['all', 'test', 'medication', 'condition', 'procedure', 'discharge'].map((t) => (
                  <button
                    key={t}
                    type="button"
                    className={`filter-tag-pill ${eventTypeFilter === t ? 'active' : ''}`}
                    onClick={() => setEventTypeFilter(t)}
                  >
                    {t === 'all' ? 'All' : t.toUpperCase()}
                  </button>
                ))}
              </div>

              <div className="filter-cluster-group">
                <span className="cluster-label">Priority:</span>
                {['all', 'Critical', 'High', 'Moderate'].map((p) => (
                  <button
                    key={p}
                    type="button"
                    className={`filter-tag-pill ${priorityFilter === p ? 'active' : ''}`}
                    onClick={() => setPriorityFilter(p)}
                  >
                    {p === 'all' ? 'All' : p}
                  </button>
                ))}
              </div>

              {(eventTypeFilter !== 'all' || priorityFilter !== 'all' || searchTerm) && (
                <button 
                  type="button" 
                  className="filter-reset-link"
                  onClick={() => {
                    setEventTypeFilter('all');
                    setPriorityFilter('all');
                    setSearchTerm('');
                  }}
                >
                  Reset
                </button>
              )}
            </div>
          </div>

          {/* Clinical Vertical Spine Chronology */}
          <div className="clinical-spine-container">
            {/* The 2px Continuous Spine Line */}
            <div className="central-vertical-spine-line" aria-hidden="true" />

            {timelineStream.items.length > 0 ? (
              timelineStream.items.map((item, idx) => {
                // RENDER DOCUMENTATION GAP INLINE
                if (item.type === 'gap') {
                  const gap = item.data;
                  return (
                    <div key={`gap-${gap.gap_id || idx}`} className="spine-entry spine-gap-entry animate-fade-in">
                      {/* Spine Marker Node (Amber) */}
                      <div className="spine-marker gap-marker" aria-hidden="true">
                        <Clock size={13} className="text-clinical-amber" />
                      </div>

                      {/* Documentation Gap Banner (Not a giant card) */}
                      <div className="inline-gap-strip">
                        <div className="gap-strip-top">
                          <div className="gap-badge-cluster">
                            <span className="badge-gap-amber font-mono">DOCUMENTATION GAP</span>
                            <strong className="gap-days-highlight">{gap.days_gap} Days Without Records</strong>
                          </div>
                          <span className="gap-dates-span font-mono">{gap.gap_start_date} → {gap.gap_end_date}</span>
                        </div>
                        <p className="gap-disclaimer-text">
                          "These gaps indicate missing documentation in the uploaded corpus and do not confirm absence of care."
                        </p>
                      </div>
                    </div>
                  );
                }

                // RENDER CLINICAL EVENT
                const ev = item.data;
                const meta = getEventCategoryMeta(ev.event_type);
                const Icon = meta.icon;
                const dateMilestones = timelineStream.milestoneMap.get(ev.event_date);
                const isFirstForDate = idx === 0 || 
                  (timelineStream.items[idx - 1]?.type === 'event' && timelineStream.items[idx - 1].data.event_date !== ev.event_date);

                return (
                  <React.Fragment key={ev.event_id || idx}>
                    {/* MILESTONE CHAPTER SEPARATOR */}
                    {isFirstForDate && dateMilestones && dateMilestones.length > 0 && (
                      <div className="milestone-chapter-separator animate-fade-in">
                        <div className="chapter-flag-icon">
                          <Flag size={13} />
                        </div>
                        <div className="chapter-label-text">
                          <span className="chapter-kicker">CARE MILESTONE:</span>
                          <strong className="chapter-title-main">{dateMilestones[0].title}</strong>
                          <span className="chapter-doc-sub">• {dateMilestones[0].document_name}</span>
                        </div>
                      </div>
                    )}

                    {/* REGULAR SPINE EVENT ENTRY */}
                    <div className={`spine-entry spine-event-entry ${meta.colorClass} animate-fade-in`}>
                      {/* Node Bullet on Spine */}
                      <div className={`spine-node-bullet ${meta.colorClass}`} aria-hidden="true">
                        <Icon size={13} />
                      </div>

                      {/* Event Content Block (Clean, compact, non-card look) */}
                      <div className="spine-event-content-block">
                        {/* Row 1: Date, Type, Priority, Source Document */}
                        <div className="spine-event-meta-row">
                          <div className="meta-left-tags">
                            <span className="event-date-stamp font-mono">{ev.event_date || 'Undated'}</span>
                            <span className={`event-type-pill ${meta.colorClass}`}>
                              {meta.label}
                            </span>
                            {getPriorityIndicator(ev.importance_priority || 'Moderate')}
                          </div>

                          <div className="meta-right-source">
                            <span className="source-doc-ref font-mono">
                              {ev.source_document_name} (p. {ev.source_page || 1})
                            </span>
                          </div>
                        </div>

                        {/* Row 2: Event Title */}
                        <div className="spine-event-title-row">
                          <h3 className="spine-event-title">{ev.event_description}</h3>
                        </div>

                        {/* Row 3: Short Evidence Quote with Subtle Teal Evidence Rail */}
                        {ev.supporting_text && (
                          <div className="spine-evidence-rail">
                            <blockquote className="evidence-quote-citation">
                              "{ev.supporting_text}"
                            </blockquote>
                          </div>
                        )}

                        {/* Row 4: Quick Action Links */}
                        <div className="spine-action-links-row">
                          <button 
                            type="button"
                            className="link-action-btn"
                            onClick={() => onSelectEvent && onSelectEvent(ev)}
                          >
                            <span>Inspect Structured Entities</span>
                            <ChevronRight size={12} />
                          </button>

                          <button 
                            type="button"
                            className="link-action-btn text-clinical-teal"
                            onClick={() => onInspectDocument && onInspectDocument(ev.source_document_id, ev.supporting_text)}
                          >
                            <ExternalLink size={12} />
                            <span>Inspect Primary Record</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  </React.Fragment>
                );
              })
            ) : (
              <div className="empty-spine-state">
                <Clock size={32} className="text-muted mb-2" />
                <p>No clinical events match the active search and filter parameters.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* SUBVIEW 2: CLINICAL ACTION CHAINS (OBSERVATION ↓ ACTION ↓ OUTCOME) */}
      {subView === 'chains' && (
        <div className="action-chains-view animate-fade-in">
          <div className="chains-orientation-header">
            <div className="orientation-kicker">CAUSAL CLINICAL DECISION FLOWS</div>
            <p className="orientation-desc">
              Longitudinal action pathways connecting diagnostic findings to specialist consults, therapeutic titration, surveillance, and acute holds.
            </p>
          </div>

          <div className="action-chains-grid">
            {chains.map((chain) => (
              <div key={chain.chain_id} className="action-chain-panel">
                <div className="chain-panel-top">
                  <div className="chain-title-wrap">
                    <h3 className="chain-main-title">{chain.chain_title}</h3>
                    <span className="chain-domain-badge">{chain.domain}</span>
                  </div>
                  <span className="chain-nodes-count font-mono text-xs text-secondary">
                    {chain.nodes?.length || 0} Connected Nodes
                  </span>
                </div>

                <p className="chain-summary-narrative">{chain.summary}</p>

                {/* Vertical Step Nodes with Arrows */}
                <div className="chain-visual-pathway">
                  {chain.nodes?.map((node, nIdx) => {
                    const stepRole = nIdx === 0 
                      ? 'OBSERVATION' 
                      : nIdx === chain.nodes.length - 1 
                        ? 'FOLLOW-UP / OUTCOME' 
                        : 'CLINICAL ACTION';

                    return (
                      <div key={node.event_id || nIdx} className="chain-path-node-wrapper">
                        <div className={`chain-path-node-box role-${stepRole.toLowerCase().replace(/[^a-z]/g, '')}`}>
                          <div className="node-role-header">
                            <span className="role-tag">{stepRole}</span>
                            <span className="node-date font-mono">{node.event_date || 'Undated'}</span>
                          </div>

                          <div className="node-clinical-desc font-medium">
                            {node.description}
                          </div>

                          <div className="node-evidence-citation-line">
                            <span className="evidence-quote-snippet">"{node.supporting_text}"</span>
                            <span className="evidence-doc-cite">• {node.source_document_name}</span>
                          </div>

                          {node.transition_explanation && (
                            <div className="node-transition-reason">
                              <span className="transition-label">Rationale:</span> {node.transition_explanation}
                            </div>
                          )}

                          <div className="node-footer-action">
                            <button 
                              type="button"
                              className="btn-inspect-chain-source"
                              onClick={() => onInspectDocument && onInspectDocument(node.source_document_id, node.supporting_text)}
                            >
                              <ExternalLink size={11} className="inline mr-1" />
                              <span>Inspect Source Record</span>
                            </button>
                          </div>
                        </div>

                        {/* Arrow to next node */}
                        {nIdx < chain.nodes.length - 1 && (
                          <div className="chain-down-arrow-container" aria-hidden="true">
                            <ArrowDown size={16} className="text-clinical-blue" />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SUBVIEW 3: JOURNEY GRAPH */}
      {subView === 'graph' && (
        <div className="journey-graph-wrapper animate-fade-in">
          <PatientJourneyGraph 
            patientId={patientId}
            onInspectDocument={onInspectDocument}
          />
        </div>
      )}
    </div>
  );
}
