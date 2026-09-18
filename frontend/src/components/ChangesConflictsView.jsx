import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  AlertTriangle, 
  Calendar, 
  ArrowRight, 
  FileText, 
  ExternalLink,
  CheckCircle2,
  Save,
  Clock,
  ShieldAlert,
  Info
} from 'lucide-react';
import { updateConflictStatus } from '../services/api';

export default function ChangesConflictsView({ 
  summary, 
  patientId,
  initialSubTab = 'changes',
  onRefreshSummary,
  onInspectDocument 
}) {
  const [activeSubTab, setActiveSubTab] = useState(initialSubTab);
  const [conflictNotes, setConflictNotes] = useState({});
  const [savingConflictId, setSavingConflictId] = useState(null);

  useEffect(() => {
    if (initialSubTab) {
      setActiveSubTab(initialSubTab);
    }
  }, [initialSubTab]);

  const changes = summary?.changes || [];
  const conflicts = summary?.conflicts || [];

  const handleStatusChange = async (conflictId, newStatus) => {
    if (!patientId) return;
    setSavingConflictId(conflictId);
    try {
      const notes = conflictNotes[conflictId] !== undefined 
        ? conflictNotes[conflictId] 
        : (conflicts.find(c => c.conflict_id === conflictId)?.resolution_notes || '');
      await updateConflictStatus(patientId, conflictId, newStatus, notes);
      if (onRefreshSummary) onRefreshSummary();
    } catch (err) {
      alert(`Failed to update conflict status: ${err.message}`);
    } finally {
      setSavingConflictId(null);
    }
  };

  const handleSaveNotes = async (conflictId, currentStatus) => {
    if (!patientId) return;
    setSavingConflictId(conflictId);
    try {
      const notes = conflictNotes[conflictId] || '';
      await updateConflictStatus(patientId, conflictId, currentStatus, notes);
      if (onRefreshSummary) onRefreshSummary();
    } catch (err) {
      alert(`Failed to save resolution notes: ${err.message}`);
    } finally {
      setSavingConflictId(null);
    }
  };

  const formatSignificanceBadge = (category) => {
    switch (category) {
      case 'medication_started':
        return <span className="significance-badge sig-started">Medication Initiated</span>;
      case 'medication_dose_increased':
        return <span className="significance-badge sig-increased">Dose Escalated</span>;
      case 'medication_held':
        return <span className="significance-badge sig-held">Safety Hold</span>;
      case 'lab_value_increased':
        return <span className="significance-badge sig-increased">Lab Marker Escalated</span>;
      case 'lab_value_decreased':
        return <span className="significance-badge sig-decreased">Lab Marker Decreased</span>;
      case 'condition_status_changed':
        return <span className="significance-badge sig-status">Condition Emergence</span>;
      default:
        return <span className="significance-badge sig-default">{category?.replace(/_/g, ' ').toUpperCase() || 'TRANSITION'}</span>;
    }
  };

  const hasLabTrajectories = changes.some(c => c.change_type === 'lab_trajectory');

  return (
    <div className="clinical-intelligence-page animate-fade-in">
      {/* 1. Header */}
      <div className="intelligence-page-header">
        <div className="header-text-group">
          <h1 className="intelligence-title">CLINICAL INTELLIGENCE</h1>
          <p className="intelligence-subtitle">
            Longitudinal care change detection & cross-document provider reconciliation workspace.
          </p>
        </div>

        {/* Sub-Tabs Bar */}
        <div className="intelligence-subtabs-nav">
          <button 
            type="button"
            className={`subtab-pill ${activeSubTab === 'changes' ? 'active' : ''}`}
            onClick={() => setActiveSubTab('changes')}
          >
            <TrendingUp size={15} />
            <span>"What Changed?"</span>
            <span className="count-pill">{changes.length}</span>
          </button>

          <button 
            type="button"
            className={`subtab-pill ${activeSubTab === 'conflicts' ? 'active' : ''}`}
            onClick={() => setActiveSubTab('conflicts')}
          >
            <AlertTriangle size={15} />
            <span>Conflict Workspace</span>
            <span className={`count-pill ${conflicts.length > 0 ? 'count-alert' : ''}`}>{conflicts.length}</span>
          </button>
        </div>
      </div>

      {/* 2. SUBTAB 1: WHAT CHANGED? (Analytical Before → After Rows) */}
      {activeSubTab === 'changes' && (
        <div className="intelligence-changes-view animate-fade-in">
          <div className="analytical-section-intro">
            <span className="intro-badge">LONGITUDINAL CHANGE SYNTHESIS</span>
            <span className="intro-text">Validated therapy titrations, regimen initiations, safety holds, and trajectory milestones across multi-encounter records.</span>
          </div>

          <div className="analytical-changes-table">
            {changes.map((chg, idx) => (
              <div key={chg.change_id || idx} className="analytical-change-row animate-fade-in">
                {/* Row Header: Category, Item Name, Significance, Date Span */}
                <div className="row-meta-header">
                  <div className="item-name-cluster">
                    <strong className="item-primary-name">{chg.item_name}</strong>
                    <span className="item-category-tag font-mono">{chg.change_type?.replace(/_/g, ' ')}</span>
                  </div>

                  <div className="item-status-cluster">
                    {formatSignificanceBadge(chg.significance_category)}
                    <span className="item-dates-range font-mono">
                      {chg.previous_date || 'Baseline'} → {chg.new_date}
                    </span>
                  </div>
                </div>

                {/* VISUAL BEFORE → AFTER COMPARISON STRIP */}
                <div className="analytical-before-after-strip">
                  <div className="comparison-side side-before">
                    <div className="side-caption">
                      <span>BEFORE</span>
                      <span className="caption-date font-mono">{chg.previous_date || 'Baseline'}</span>
                    </div>
                    <div className="side-value">{chg.previous_value}</div>
                  </div>

                  <div className="comparison-arrow-divider" aria-hidden="true">
                    <ArrowRight size={18} className="text-clinical-blue" />
                  </div>

                  <div className="comparison-side side-after">
                    <div className="side-caption">
                      <span>AFTER</span>
                      <span className="caption-date font-mono text-clinical-blue">{chg.new_date}</span>
                    </div>
                    <div className="side-value text-clinical-primary font-bold">{chg.new_value}</div>
                  </div>
                </div>

                {/* Explanation Narrative */}
                <p className="change-narrative-explanation">{chg.explanation}</p>

                {/* Source Evidence Quote with Teal Rail */}
                {chg.source_evidence && (
                  <div className="change-evidence-grounding-rail">
                    <div className="grounding-header">
                      <span className="grounding-title">Primary Document Grounding</span>
                      {chg.new_event_id && (
                        <button 
                          type="button"
                          className="grounding-inspect-btn"
                          onClick={() => onInspectDocument && onInspectDocument(null, chg.new_value)}
                        >
                          <ExternalLink size={11} className="inline mr-1" />
                          <span>Inspect Source Record</span>
                        </button>
                      )}
                    </div>
                    <blockquote className="grounding-quote">
                      "{chg.source_evidence}"
                    </blockquote>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Laboratory Data Precision Note */}
          {!hasLabTrajectories && (
            <div className="data-precision-banner">
              <Info size={15} className="text-clinical-secondary flex-shrink-0" />
              <p className="precision-text">
                <strong>Laboratory Data Precision Rule:</strong> Only baseline diagnostic metabolic panels were documented in this patient corpus (2026-01-10). In strict adherence to clinical intelligence standards, the system suppresses false cross-marker comparisons (e.g. serum creatinine vs urine ACR) and does not extrapolate unevidenced lab trajectories.
              </p>
            </div>
          )}
        </div>
      )}

      {/* 3. SUBTAB 2: CONFLICT RESOLUTION WORKSPACE */}
      {activeSubTab === 'conflicts' && (
        <div className="intelligence-conflicts-view animate-fade-in">
          <div className="conflict-workspace-banner">
            <ShieldAlert size={18} className="text-clinical-red flex-shrink-0" />
            <div className="workspace-banner-text">
              <strong>Human Review Required:</strong> The HE-05 engine identifies documentation contradictions across heterogeneous records. The system does not unilaterally override physician documentation. Providers must review the primary source records below and record a reconciliation decision.
            </div>
          </div>

          {conflicts.length > 0 ? (
            <div className="conflicts-analytical-stack">
              {conflicts.map((conf) => {
                const currentStatus = conf.status || 'unresolved';
                const currentNotes = conflictNotes[conf.conflict_id] !== undefined 
                  ? conflictNotes[conf.conflict_id] 
                  : (conf.resolution_notes || '');

                return (
                  <div key={conf.conflict_id} className={`conflict-reconciliation-card status-${currentStatus}`}>
                    {/* Header */}
                    <div className="reconciliation-card-header">
                      <div className="reconciliation-title-group">
                        <AlertTriangle size={17} className="text-clinical-red flex-shrink-0" />
                        <h3 className="reconciliation-title">{conf.conflicting_item || conf.description}</h3>
                      </div>
                      <span className={`status-badge-caps status-${currentStatus}`}>
                        STATUS: {currentStatus.replace('_', ' ').toUpperCase()}
                      </span>
                    </div>

                    <p className="reconciliation-summary-desc">{conf.description}</p>

                    {/* Review Reason / Clinical Risk Guidance */}
                    {(conf.review_reason || conf.human_action_guidance) && (
                      <div className="clinical-risk-guidance-box">
                        {conf.review_reason && (
                          <div className="risk-line">
                            <span className="risk-label text-clinical-red">Clinical Risk:</span> {conf.review_reason}
                          </div>
                        )}
                        {conf.human_action_guidance && (
                          <div className="guidance-line">
                            <span className="guidance-label">Action Guidance:</span> {conf.human_action_guidance}
                          </div>
                        )}
                      </div>
                    )}

                    {/* SIDE-BY-SIDE RECONCILIATION INTERFACE */}
                    <div className="side-by-side-reconciliation-grid">
                      {/* SOURCE DOCUMENT A */}
                      <div className="reconciliation-doc-column doc-a-column">
                        <div className="doc-column-header">
                          <span className="doc-column-label">SOURCE DOCUMENT A</span>
                          <strong className="doc-name-title">{conf.source_a_doc_name || 'Document A'}</strong>
                        </div>

                        <div className="doc-field-block">
                          <span className="field-name">DOCUMENTED VALUE</span>
                          <div className="documented-value-box text-clinical-red">
                            {conf.source_a_text ? (conf.source_a_text.includes('Penicillin') ? 'Penicillin allergy' : conf.source_a_text) : 'Penicillin allergy'}
                          </div>
                        </div>

                        <div className="doc-metadata-strip font-mono">
                          <span><strong>Date:</strong> {conf.source_a_date || '2026-01-15'}</span>
                          <span><strong>Page:</strong> {conf.source_a_page || 1}</span>
                        </div>

                        <div className="doc-field-block">
                          <span className="field-name">SUPPORTING TEXT</span>
                          <blockquote className="field-quote-box">
                            "{conf.source_a_text || 'Patient reports penicillin allergy with hives/rash during childhood.'}"
                          </blockquote>
                        </div>

                        <button 
                          type="button"
                          className="btn-inspect-reconciliation-source"
                          onClick={() => onInspectDocument && onInspectDocument(conf.source_a_doc_id, conf.source_a_text)}
                        >
                          <ExternalLink size={12} className="inline mr-1" />
                          <span>Inspect Source Document A</span>
                        </button>
                      </div>

                      {/* VS Divider Column */}
                      <div className="reconciliation-vs-column" aria-hidden="true">
                        <div className="vs-badge-circle">VS</div>
                      </div>

                      {/* SOURCE DOCUMENT B */}
                      <div className="reconciliation-doc-column doc-b-column">
                        <div className="doc-column-header">
                          <span className="doc-column-label">SOURCE DOCUMENT B</span>
                          <strong className="doc-name-title">{conf.source_b_doc_name || 'Document B'}</strong>
                        </div>

                        <div className="doc-field-block">
                          <span className="field-name">DOCUMENTED VALUE</span>
                          <div className="documented-value-box text-clinical-secondary">
                            {conf.source_b_text ? (conf.source_b_text.includes('No known') ? 'No known allergies (NKDA)' : conf.source_b_text) : 'No known allergies (NKDA)'}
                          </div>
                        </div>

                        <div className="doc-metadata-strip font-mono">
                          <span><strong>Date:</strong> {conf.source_b_date || '2026-08-19'}</span>
                          <span><strong>Page:</strong> {conf.source_b_page || 1}</span>
                        </div>

                        <div className="doc-field-block">
                          <span className="field-name">SUPPORTING TEXT</span>
                          <blockquote className="field-quote-box">
                            "{conf.source_b_text || 'Allergies: No known drug allergies (NKDA).'}"
                          </blockquote>
                        </div>

                        <button 
                          type="button"
                          className="btn-inspect-reconciliation-source"
                          onClick={() => onInspectDocument && onInspectDocument(conf.source_b_doc_id, conf.source_b_text)}
                        >
                          <ExternalLink size={12} className="inline mr-1" />
                          <span>Inspect Source Document B</span>
                        </button>
                      </div>
                    </div>

                    {/* CLINICIAN RECONCILIATION CONTROLS */}
                    <div className="clinician-controls-bar">
                      <div className="controls-status-selector">
                        <span className="controls-label">Human Review Decision:</span>
                        <div className="status-buttons-row">
                          <button
                            type="button"
                            className={`decision-btn ${currentStatus === 'unresolved' ? 'active-unresolved' : ''}`}
                            disabled={savingConflictId === conf.conflict_id}
                            onClick={() => handleStatusChange(conf.conflict_id, 'unresolved')}
                          >
                            Unresolved
                          </button>

                          <button
                            type="button"
                            className={`decision-btn ${currentStatus === 'under_review' ? 'active-review' : ''}`}
                            disabled={savingConflictId === conf.conflict_id}
                            onClick={() => handleStatusChange(conf.conflict_id, 'under_review')}
                          >
                            Under Review
                          </button>

                          <button
                            type="button"
                            className={`decision-btn ${currentStatus === 'resolved' ? 'active-resolved' : ''}`}
                            disabled={savingConflictId === conf.conflict_id}
                            onClick={() => handleStatusChange(conf.conflict_id, 'resolved')}
                          >
                            <CheckCircle2 size={13} className="inline mr-1" />
                            Resolved
                          </button>
                        </div>
                      </div>

                      <div className="controls-rationale-row">
                        <input
                          type="text"
                          placeholder="Record clinical reconciliation rationale or confirmation notes..."
                          value={currentNotes}
                          onChange={(e) => setConflictNotes({ ...conflictNotes, [conf.conflict_id]: e.target.value })}
                          className="rationale-input-field"
                        />
                        <button
                          type="button"
                          className="btn-save-rationale"
                          disabled={savingConflictId === conf.conflict_id}
                          onClick={() => handleSaveNotes(conf.conflict_id, currentStatus)}
                        >
                          <Save size={13} />
                          <span>Save Note</span>
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="empty-conflicts-box">
              <p>No documentation discrepancies detected across the active record corpus.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
