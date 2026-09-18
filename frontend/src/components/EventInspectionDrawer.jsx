import React, { useEffect } from 'react';
import { 
  X, 
  Clock, 
  Calendar, 
  FileText, 
  ShieldCheck, 
  ExternalLink, 
  Layers, 
  GitBranch, 
  ArrowRight,
  Flame,
  Zap,
  Activity,
  Pill,
  Stethoscope,
  Scan,
  LogOut
} from 'lucide-react';

export default function EventInspectionDrawer({ 
  event, 
  isOpen, 
  onClose, 
  onInspectDocument 
}) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !event) return null;

  const getEventIcon = (type) => {
    switch (type) {
      case 'test': return <Activity size={16} className="text-cyan" />;
      case 'medication': return <Pill size={16} className="text-emerald" />;
      case 'condition': return <Stethoscope size={16} className="text-purple" />;
      case 'procedure': return <Scan size={16} className="text-indigo" />;
      case 'discharge': return <LogOut size={16} className="text-rose" />;
      default: return <Clock size={16} className="text-blue" />;
    }
  };

  const getPriorityBadge = (priority) => {
    switch (priority) {
      case 'Critical':
        return <span className="badge-pill badge-priority-critical">🔥 Critical</span>;
      case 'High':
        return <span className="badge-pill badge-priority-high">⚡ High</span>;
      case 'Moderate':
        return <span className="badge-pill badge-priority-moderate">Moderate</span>;
      default:
        return <span className="badge-pill badge-priority-info">Informational</span>;
    }
  };

  const getCertaintyBadge = (certainty) => {
    switch (certainty) {
      case 'explicit':
        return <span className="badge-pill badge-certainty-explicit">Explicit Date</span>;
      case 'relative':
        return <span className="badge-pill badge-certainty-relative">Relative Date</span>;
      case 'approximate':
        return <span className="badge-pill badge-certainty-approximate">Approximate</span>;
      default:
        return <span className="badge-pill badge-certainty-unknown">Undated</span>;
    }
  };

  return (
    <div className="drawer-backdrop animate-fade-in" onClick={onClose}>
      <div 
        className="drawer-panel event-inspection-drawer animate-slide-left" 
        onClick={(e) => e.stopPropagation()}
      >
        {/* Drawer Header */}
        <div className="drawer-header">
          <div className="drawer-header-titles">
            <div className="flex items-center gap-2 mb-1">
              <span className="badge-pill badge-primary">
                {event.event_type?.replace('_', ' ').toUpperCase()}
              </span>
              {getPriorityBadge(event.importance_priority || 'Moderate')}
            </div>
            <h3 className="drawer-title">{event.event_description}</h3>
          </div>
          <button className="drawer-close-btn" onClick={onClose} title="Close inspection (Esc)">
            <X size={20} />
          </button>
        </div>

        {/* Drawer Body Content */}
        <div className="drawer-body event-drawer-body">
          {/* Primary Action Button */}
          <div className="drawer-primary-action">
            <button 
              className="btn btn-primary w-full"
              onClick={() => onInspectDocument(event.source_document_id, event.supporting_text)}
            >
              <ExternalLink size={15} />
              <span>Inspect Source Record in Evidence Drawer</span>
            </button>
          </div>

          {/* Temporal & Certainty Section */}
          <div className="drawer-section">
            <h4 className="drawer-section-title">
              <Clock size={15} className="text-cyan" />
              <span>Temporal Verification</span>
            </h4>
            <div className="drawer-card-grid">
              <div className="drawer-meta-card">
                <span className="drawer-meta-label">Documented Event Date</span>
                <span className="drawer-meta-val"><strong>{event.event_date || 'Date Undetermined'}</strong></span>
                <span className="drawer-meta-hint">Occurred during documented encounter</span>
              </div>

              <div className="drawer-meta-card">
                <span className="drawer-meta-label">Temporal Certainty</span>
                <div className="mt-1 mb-1">{getCertaintyBadge(event.event_date_type)}</div>
                <span className="drawer-meta-hint">
                  {event.event_date_type === 'explicit' ? 'Strictly confirmed by calendar date in source' :
                   event.event_date_type === 'relative' ? 'Inferred relative to anchor event' :
                   event.event_date_type === 'approximate' ? 'Historical clinical timeframe' :
                   'No calendar date found in record'}
                </span>
              </div>
            </div>
          </div>

          {/* Clinical Priority & Evidence Grounding Section */}
          <div className="drawer-section">
            <h4 className="drawer-section-title">
              <ShieldCheck size={15} className="text-teal" />
              <span>Priority & Evidence Confidence</span>
            </h4>
            
            <div className="drawer-info-box">
              <div className="mb-2">
                <strong className="text-xs text-secondary block mb-1">Clinical Priority Rationale:</strong>
                <p className="text-sm text-primary">
                  {event.importance_reason || 'Categorized based on acute vs baseline clinical guidelines.'}
                </p>
              </div>

              <div>
                <strong className="text-xs text-secondary block mb-1">Evidence Grounding Rationale:</strong>
                <p className="text-sm text-primary">
                  {event.evidence_rationale || 'Grounding level assigned based on objective vs subjective provider documentation.'}
                </p>
              </div>
            </div>
          </div>

          {/* Supporting Evidence Quote Box */}
          <div className="drawer-section">
            <h4 className="drawer-section-title">
              <FileText size={15} className="text-cyan" />
              <span>Primary Source Evidence Quote</span>
            </h4>

            <div className="drawer-evidence-quote-box">
              <blockquote className="drawer-evidence-quote">
                "{event.supporting_text}"
              </blockquote>
              <div className="drawer-evidence-origin">
                <span>Source Document: <strong>{event.source_document_name}</strong></span>
                <span>Page {event.source_page || 1}</span>
              </div>
            </div>
          </div>

          {/* Structured Clinical Entities */}
          {event.structured_data && (
            <div className="drawer-section">
              <h4 className="drawer-section-title">
                <Layers size={15} className="text-purple" />
                <span>Extracted Clinical Entities</span>
              </h4>

              <div className="drawer-entities-list">
                {event.structured_data.tests?.map((t, i) => (
                  <div key={i} className="drawer-entity-pill entity-test">
                    <strong>Test:</strong> {t.name} = {t.value} {t.unit} ({t.status})
                  </div>
                ))}
                {event.structured_data.medications?.map((m, i) => (
                  <div key={i} className="drawer-entity-pill entity-med">
                    <strong>Medication:</strong> {m.name} {m.dose} ({m.freq})
                  </div>
                ))}
                {event.structured_data.conditions?.map((c, i) => (
                  <div key={i} className="drawer-entity-pill entity-cond">
                    <strong>Condition:</strong> {c}
                  </div>
                ))}
                {event.structured_data.procedures?.map((p, i) => (
                  <div key={i} className="drawer-entity-pill entity-proc">
                    <strong>Procedure:</strong> {p}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Related Clinical Events */}
          {event.related_events && event.related_events.length > 0 && (
            <div className="drawer-section">
              <h4 className="drawer-section-title">
                <GitBranch size={15} className="text-indigo" />
                <span>Clinically Connected Events ({event.related_events.length})</span>
              </h4>

              <div className="drawer-relationships-list">
                {event.related_events.map((rel, idx) => (
                  <div key={idx} className="drawer-rel-card">
                    <div className="drawer-rel-header">
                      <span className="badge-pill badge-primary text-xs">
                        {rel.relationship_type?.replace('_', ' ').toUpperCase()}
                      </span>
                      <span className="text-xs text-muted">{rel.related_event_date || 'Date Undated'}</span>
                    </div>
                    <p className="drawer-rel-desc">
                      <ArrowRight size={13} className="inline mr-1 text-cyan" />
                      {rel.related_event_desc}
                    </p>
                    {rel.explanation && (
                      <p className="drawer-rel-expl">{rel.explanation}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Drawer Footer */}
        <div className="drawer-footer">
          <button 
            className="btn btn-sm btn-outline"
            onClick={() => onInspectDocument(event.source_document_id, event.supporting_text)}
          >
            <ExternalLink size={13} />
            <span>Open in Source Viewer</span>
          </button>
          <button className="btn btn-sm btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
