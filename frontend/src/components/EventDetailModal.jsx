import React from 'react';
import { 
  X, 
  Clock, 
  FileText, 
  GitBranch, 
  ExternalLink, 
  ShieldCheck, 
  Calendar,
  Layers,
  ArrowRight
} from 'lucide-react';

export default function EventDetailModal({ 
  event, 
  onClose, 
  onInspectDocument 
}) {
  if (!event) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card animate-fade-in" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <div className="modal-title-cluster">
            <span className="badge-pill badge-primary">
              {event.event_type.replace('_', ' ').toUpperCase()}
            </span>
            <h2 className="modal-title">{event.event_description}</h2>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close dialog">
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {/* Temporal Comparison Grid */}
          <div className="detail-grid">
            <div className="detail-item">
              <div className="detail-item-header">
                <Clock size={15} className="text-cyan" />
                <span>Actual Event Date</span>
              </div>
              <div className="detail-item-value">
                <strong>{event.event_date || 'Date Undetermined'}</strong>
                <span className="text-xs text-muted"> (When medical event occurred)</span>
              </div>
            </div>

            <div className="detail-item">
              <div className="detail-item-header">
                <Calendar size={15} className="text-teal" />
                <span>Date Certainty</span>
              </div>
              <div className="detail-item-value">
                <span className={`badge-pill badge-certainty-${event.event_date_type}`}>
                  {event.event_date_type.toUpperCase()}
                </span>
                <span className="text-xs text-muted">
                  {event.event_date_type === 'explicit' ? 'Strictly confirmed by calendar date in source' :
                   event.event_date_type === 'relative' ? 'Inferred relative to anchor event' :
                   event.event_date_type === 'approximate' ? 'Historical / approximate clinical timeframe' :
                   'No calendar date found in record'}
                </span>
              </div>
            </div>

            <div className="detail-item">
              <div className="detail-item-header">
                <FileText size={15} className="text-indigo" />
                <span>Source Document</span>
              </div>
              <div className="detail-item-value">
                <strong>{event.source_document_name}</strong>
                <span className="text-xs text-muted">Page {event.source_page || 1} • Type: {event.source_document_type}</span>
              </div>
            </div>

            <div className="detail-item">
              <div className="detail-item-header">
                <ShieldCheck size={15} className="text-emerald" />
                <span>Extraction Confidence</span>
              </div>
              <div className="detail-item-value">
                <strong>{(event.confidence * 100).toFixed(0)}% Verified</strong>
                <span className="text-xs text-muted">Strict Schema Match</span>
              </div>
            </div>
          </div>

          {/* Source Evidence Quote Box */}
          <div className="detail-section">
            <h4 className="detail-section-title">
              <FileText size={15} className="text-cyan" />
              <span>Verbatim Source Evidence Quote</span>
            </h4>
            <div className="evidence-modal-box">
              <p className="evidence-modal-quote">"{event.supporting_text}"</p>
              <div className="evidence-modal-source">
                Recorded in <strong>{event.source_document_name}</strong> (Page {event.source_page || 1})
              </div>
            </div>
          </div>

          {/* Structured Data / Entities if present */}
          {event.structured_data && (
            <div className="detail-section">
              <h4 className="detail-section-title">
                <Layers size={15} className="text-purple" />
                <span>Extracted Entities</span>
              </h4>
              <div className="entities-chip-container">
                {event.structured_data.tests?.map((t, i) => (
                  <span key={i} className="entity-chip chip-test">
                    <strong>Test:</strong> {t.name} = {t.value} {t.unit} ({t.status})
                  </span>
                ))}
                {event.structured_data.medications?.map((m, i) => (
                  <span key={i} className="entity-chip chip-med">
                    <strong>Med:</strong> {m.name} {m.dose} ({m.freq})
                  </span>
                ))}
                {event.structured_data.conditions?.map((c, i) => (
                  <span key={i} className="entity-chip chip-condition">
                    <strong>Condition:</strong> {c}
                  </span>
                ))}
                {event.structured_data.procedures?.map((p, i) => (
                  <span key={i} className="entity-chip chip-procedure">
                    <strong>Procedure:</strong> {p}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Connected Relationships */}
          {event.related_events && event.related_events.length > 0 && (
            <div className="detail-section">
              <h4 className="detail-section-title">
                <GitBranch size={15} className="text-teal" />
                <span>Clinically Connected Events ({event.related_events.length})</span>
              </h4>
              <div className="related-events-list">
                {event.related_events.map((rel, idx) => (
                  <div key={idx} className="related-event-card">
                    <div className="related-event-header">
                      <span className="badge-pill badge-primary text-xs">
                        {rel.relationship_type.replace('_', ' ').toUpperCase()}
                      </span>
                      <span className="text-xs text-muted">{rel.related_event_date || 'Date Undated'}</span>
                    </div>
                    <p className="related-event-desc">
                      <ArrowRight size={13} className="inline mr-1 text-cyan" />
                      {rel.related_event_desc}
                    </p>
                    {rel.explanation && (
                      <p className="text-xs text-secondary mt-1">{rel.explanation}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="modal-footer">
          <button 
            className="btn btn-outline"
            onClick={() => onInspectDocument(event.source_document_id, event.supporting_text)}
          >
            <ExternalLink size={15} />
            <span> at Cited Snippet</span>
          </button>
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
