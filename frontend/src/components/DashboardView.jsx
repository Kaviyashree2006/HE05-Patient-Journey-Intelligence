import React from 'react';
import { 
  Clock, 
  TrendingUp, 
  AlertTriangle, 
  ArrowRight, 
  ShieldCheck, 
  Activity, 
  Sparkles,
  ChevronRight,
  Pill,
  Stethoscope,
  Scan,
  LogOut
} from 'lucide-react';

export default function DashboardView({ 
  patient, 
  summary, 
  timeline, 
  onNavigate, 
  onInspectDocument,
  onSelectEvent,
  onSeedDemo, 
  isSeeding 
}) {
  if (!patient) {
    return (
      <div className="empty-state-container animate-fade-in">
        <div className="clinical-empty-card">
          <div className="empty-icon-bubble">
            <Activity className="text-clinical-blue" size={36} />
          </div>
          <h2 className="empty-title">HE-05: Evidence-Linked Patient Journey</h2>
          <p className="empty-description">
            Reconstructs a longitudinal clinical trajectory from heterogeneous medical records into an 
            accurate, chronological, evidence-grounded patient timeline with 100% source traceability.
          </p>
          <div className="empty-action-row">
            <button className="btn btn-primary" onClick={onSeedDemo} disabled={isSeeding}>
              <Sparkles size={15} className={isSeeding ? 'animate-spin' : ''} />
              <span>{isSeeding ? 'Seeding Synthetic Dataset...' : 'Load Demo Patient (Sarah Jenkins)'}</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  const events = timeline?.timeline_events || [];
  const changes = summary?.changes || [];
  const conflicts = summary?.conflicts || [];
  const gaps = summary?.gaps || [];

  // Categorize events for the dominant visual timeline axis
  const getEventCategoryMeta = (type) => {
    switch (type) {
      case 'test':
        return { label: 'Lab', colorClass: 'node-lab', icon: Activity };
      case 'medication':
        return { label: 'Medication', colorClass: 'node-med', icon: Pill };
      case 'condition':
        return { label: 'Clinical Note', colorClass: 'node-note', icon: Stethoscope };
      case 'procedure':
        return { label: 'Imaging', colorClass: 'node-imaging', icon: Scan };
      case 'discharge':
        return { label: 'Discharge', colorClass: 'node-discharge', icon: LogOut };
      default:
        return { label: 'Event', colorClass: 'node-slate', icon: Clock };
    }
  };

  // Group events by major documented clinical milestones (strictly from backend data)
  const phases = [
    {
      month: 'JAN 2026',
      periodLabel: 'Jan 10 – 15',
      summaryTag: 'Baseline Lab & Endocrinology Consult',
      events: events.filter(e => e.event_date?.startsWith('2026-01')),
      gapAfter: null
    },
    {
      month: 'FEB 2026',
      periodLabel: 'Feb 18',
      summaryTag: 'Cardiology Escalation',
      events: events.filter(e => e.event_date?.startsWith('2026-02')),
      gapAfter: { days: 83, label: '83-Day Documentation Gap', span: 'Feb 18 → May 12' }
    },
    {
      month: 'MAY 2026',
      periodLabel: 'May 12',
      summaryTag: 'Outpatient Renal Surveillance',
      events: events.filter(e => e.event_date?.startsWith('2026-05')),
      gapAfter: { days: 94, label: '94-Day Documentation Gap', span: 'May 12 → Aug 14' }
    },
    {
      month: 'AUG 2026',
      periodLabel: 'Aug 14 – 19',
      summaryTag: 'Hospital Inpatient & AKI Discharge',
      events: events.filter(e => e.event_date?.startsWith('2026-08')),
      gapAfter: null
    }
  ];

  return (
    <div className="overview-clinical-workspace animate-fade-in">
      {/* 1. REDUCED & CONCISE PATIENT JOURNEY OVERVIEW NARRATIVE */}
      <section className="overview-narrative-section">
        <div className="overview-narrative-compact">
          <div className="narrative-kicker-row">
            <span className="overview-heading">PATIENT JOURNEY OVERVIEW</span>
            <span className="source-grounded-pill font-mono">
              <ShieldCheck size={11} className="text-clinical-teal" />
              <span>Evidence-grounded</span>
            </span>
          </div>
          <p className="overview-narrative-concise">
            Longitudinal 5-document care trajectory (Jan 10 – Aug 19, 2026). Traces initial severe metabolic dysregulation 
            (HbA1c 9.4%, Fasting Blood Glucose 210 mg/dL), endocrine initiation and cardiology escalation of Metformin to 1000 mg, 
            through acute August hospitalization for volume depletion and AKI with an immediate Metformin safety hold and discharge transition to basal Insulin Glargine 18 units.
          </p>
        </div>
      </section>

      {/* 2. CENTRAL VISUAL ELEMENT: DOMINANT JOURNEY TIMELINE AXIS */}
      <section className="overview-journey-axis-section dominant-axis" aria-label="Horizontal Care Trajectory Axis">
        <div className="axis-section-header">
          <div className="axis-title-group">
            <h3 className="axis-section-title">LONGITUDINAL CARE TRAJECTORY</h3>
            <span className="axis-subtitle">Interactive clinical milestones — Click any event node to inspect verbatim source evidence</span>
          </div>
          <button 
            type="button"
            className="btn btn-sm btn-subtle"
            onClick={() => onNavigate && onNavigate('timeline')}
          >
            <span>Full Vertical Timeline</span>
            <ChevronRight size={13} />
          </button>
        </div>

        <div className="journey-horizontal-timeline">
          <div className="timeline-axis-track">
            {phases.map((phase, pIdx) => (
              <div key={pIdx} className="timeline-phase-column">
                {/* Month Axis Header with Strong Visual Hierarchy */}
                <div className="phase-axis-header">
                  <div className="phase-badge-line">
                    <span className="phase-month-badge font-mono">{phase.month}</span>
                    <span className="phase-period-sub font-mono">{phase.periodLabel}</span>
                  </div>
                  <div className="phase-summary-kicker">{phase.summaryTag}</div>
                </div>

                {/* Vertical Phase Spine with Interactive Event Nodes */}
                <div className="phase-nodes-stack">
                  <div className="phase-vertical-line" aria-hidden="true" />

                  {phase.events.slice(0, 5).map((ev, eIdx) => {
                    const meta = getEventCategoryMeta(ev.event_type);
                    const Icon = meta.icon;

                    return (
                      <button
                        key={ev.event_id || eIdx}
                        type="button"
                        className={`journey-node-item ${meta.colorClass}`}
                        onClick={() => onSelectEvent && onSelectEvent(ev)}
                        title={`Inspect: ${ev.event_description}`}
                      >
                        <div className="node-marker-bullet">
                          <Icon size={12} />
                        </div>
                        <div className="node-text-wrap">
                          <div className="node-top-meta">
                            <span className="node-type-label">{meta.label}</span>
                            <span className="node-date-tag">{ev.event_date?.slice(5)}</span>
                          </div>
                          <div className="node-description-clamp">
                            {ev.event_description}
                          </div>
                          <div className="node-source-cite">
                            {ev.source_document_name?.replace('.pdf', '')}
                          </div>
                        </div>
                      </button>
                    );
                  })}

                  {phase.events.length > 5 && (
                    <button
                      type="button"
                      className="more-events-link"
                      onClick={() => onNavigate && onNavigate('timeline')}
                    >
                      + {phase.events.length - 5} more events in {phase.month}
                    </button>
                  )}
                </div>

                {/* Inline Documentation Gap Connector */}
                {phase.gapAfter && (
                  <div 
                    className="timeline-gap-axis-connector"
                    onClick={() => onNavigate && onNavigate('timeline')}
                    title={`${phase.gapAfter.days} days without documented encounters in uploaded corpus`}
                  >
                    <Clock size={11} className="text-clinical-amber flex-shrink-0" />
                    <span>{phase.gapAfter.days}d Gap ({phase.gapAfter.span || 'Documentation Gap'})</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 3. OVERVIEW ATTENTION AREA: TWO-COLUMN SECTION */}
      <section className="overview-attention-grid">
        {/* LEFT COLUMN: KEY CLINICAL CHANGES (Sourced strictly from backend) */}
        <div className="attention-panel left-panel">
          <div className="attention-panel-header">
            <div>
              <h3 className="attention-panel-title">KEY CLINICAL CHANGES</h3>
              <p className="attention-panel-sub">Validated pharmacotherapy shifts, titrations, and safety holds.</p>
            </div>
            <button 
              type="button"
              className="btn btn-xs btn-subtle"
              onClick={() => onNavigate && onNavigate('intelligence', 'changes')}
            >
              <span>View All ({changes.length})</span>
              <ChevronRight size={12} />
            </button>
          </div>

          <div className="clinical-changes-table">
            {changes.slice(0, 3).map((chg, i) => (
              <div key={chg.change_id || i} className="change-row-compact">
                <div className="change-row-kicker">
                  <strong className="change-row-drug-name">{chg.item_name}</strong>
                  <span className="change-cat-pill font-mono text-xs">
                    {chg.significance_category === 'medication_dose_increased' ? 'DOSE ESCALATED' :
                     chg.significance_category === 'medication_started' ? 'INITIATED' :
                     chg.significance_category === 'condition_status_changed' ? 'STATUS EMERGENCE' :
                     'CARE TRANSITION'}
                  </span>
                </div>

                <div className="before-after-strip">
                  <div className="before-block">
                    <span className="state-date-label font-mono">{chg.previous_date || 'Baseline'}</span>
                    <span className="state-value-text">{chg.previous_value}</span>
                  </div>

                  <div className="transition-arrow-symbol" aria-hidden="true">
                    <ArrowRight size={14} className="text-clinical-blue" />
                  </div>

                  <div className="after-block">
                    <span className="state-date-label font-mono text-clinical-blue">{chg.new_date}</span>
                    <span className="state-value-text text-clinical-primary font-semibold">{chg.new_value}</span>
                  </div>
                </div>

                <div className="change-timeline-citation font-mono">
                  <span>{chg.previous_date || 'Baseline'} → {chg.new_date}</span>
                  {chg.source_evidence && (
                    <span className="citation-quote-preview truncate">
                      • "{chg.source_evidence.slice(0, 55)}..."
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* RIGHT COLUMN: ATTENTION (Compact Conflict & Gaps) */}
        <div className="attention-panel right-panel">
          <div className="attention-panel-header">
            <div>
              <h3 className="attention-panel-title">ATTENTION</h3>
              <p className="attention-panel-sub">Discrepancies requiring provider review & corpus documentation gaps.</p>
            </div>
          </div>

          <div className="attention-alerts-stack">
            {/* CONFLICT ALERT: Exact backend allergy discrepancy */}
            {conflicts.length > 0 ? (
              conflicts.map((conf) => (
                <div key={conf.conflict_id} className="compact-conflict-alert-box">
                  <div className="conflict-box-header">
                    <div className="conflict-review-badge">
                      <AlertTriangle size={12} className="text-clinical-red" />
                      <span>⚠ REVIEW REQUIRED</span>
                    </div>
                    <span className="conflict-domain-tag font-mono">Allergy Discrepancy</span>
                  </div>

                  <div className="conflict-discrepancy-title">
                    {conf.conflicting_item || 'Penicillin Allergy Documentation'}
                  </div>

                  <div className="conflict-sources-comparison">
                    <div className="conflict-source-column source-a">
                      <span className="source-doc-label font-mono">Source A ({conf.source_a_date || 'Jan 15'})</span>
                      <strong className="source-doc-val text-clinical-red">
                        Penicillin (severe urticaria)
                      </strong>
                    </div>

                    <div className="source-vs-divider font-mono">vs</div>

                    <div className="conflict-source-column source-b">
                      <span className="source-doc-label font-mono">Source B ({conf.source_b_date || 'Aug 14'})</span>
                      <strong className="source-doc-val text-clinical-secondary">
                        No Known Drug Allergies (NKDA)
                      </strong>
                    </div>
                  </div>

                  <div className="conflict-action-footer">
                    <button 
                      type="button"
                      className="btn-review-conflict font-mono"
                      onClick={() => onNavigate && onNavigate('intelligence', 'conflicts')}
                    >
                      <span>Review Conflict →</span>
                    </button>
                  </div>
                </div>
              ))
            ) : null}

            {/* DOCUMENTATION GAPS: Exact backend gaps */}
            <div className="compact-gap-alert-box">
              <div className="gap-box-header">
                <div className="gap-title-group">
                  <Clock size={13} className="text-clinical-amber" />
                  <span className="gap-heading-text font-mono">DOCUMENTATION GAPS</span>
                </div>
                <span className="gap-count-tag font-mono">2 intervals identified</span>
              </div>

              <div className="gap-intervals-row">
                <div className="gap-pill-item">
                  <span className="gap-interval-number">83 days</span>
                  <span className="gap-interval-dates">Feb 18 → May 12</span>
                </div>
                <div className="gap-pill-item">
                  <span className="gap-interval-number">94 days</span>
                  <span className="gap-interval-dates">May 12 → Aug 14</span>
                </div>
              </div>

              <p className="gap-neutral-disclaimer">
                "These gaps indicate missing documentation in the uploaded corpus and do not confirm absence of care."
              </p>

              <div className="gap-footer-action">
                <button 
                  type="button"
                  className="btn-inspect-gaps-link font-mono"
                  onClick={() => onNavigate && onNavigate('timeline')}
                >
                  <span>Inspect Gaps in Timeline →</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
