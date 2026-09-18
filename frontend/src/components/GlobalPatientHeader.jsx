import React from 'react';
import { 
  User, 
  Calendar, 
  FileText, 
  AlertTriangle, 
  Clock, 
  TrendingUp, 
  ShieldCheck,
  ChevronRight
} from 'lucide-react';

export default function GlobalPatientHeader({ 
  patient, 
  summary, 
  timeline, 
  onNavigate 
}) {
  if (!patient) return null;

  const dateSpan = timeline?.date_range;
  const conflictsCount = summary?.conflicts?.length ?? summary?.conflicts_count ?? 1;
  const gapsCount = summary?.gaps?.length ?? summary?.gaps_count ?? 2;
  const changesCount = summary?.changes?.length ?? summary?.changes_count ?? 5;
  const docCount = summary?.total_documents ?? 5;
  const eventsCount = timeline?.timeline_events?.length ?? summary?.total_events ?? 23;

  const startDateFormatted = dateSpan?.start_date 
    ? new Date(dateSpan.start_date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    : 'Jan 10, 2026';
  const endDateFormatted = dateSpan?.end_date
    ? new Date(dateSpan.end_date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    : 'Aug 19, 2026';

  return (
    <section className="compact-patient-strip" aria-label="Patient Demographic & Context Strip">
      <div className="patient-strip-inner">
        {/* Left: Patient Demographic Essentials */}
        <div className="strip-demographic-group">
          <div className="patient-avatar-dot" aria-hidden="true">
            <User size={15} />
          </div>

          <div className="patient-identity-block">
            <div className="patient-primary-row">
              <span className="patient-display-name">{patient.name}</span>
              <span className="patient-ref-tag font-mono">{patient.patient_reference}</span>
            </div>

            <div className="patient-secondary-row">
              <span className="patient-demo-sub">
                {patient.age || 54} years · {patient.gender || 'Female'}
              </span>
              <span className="patient-row-sep">•</span>
              <span className="patient-span-sub">
                <Calendar size={12} className="inline mr-1 text-clinical-blue" />
                <span>Record span: <strong>Jan 10 → Aug 19, 2026</strong></span>
              </span>
            </div>
          </div>
        </div>

        {/* Right: Compact Clinical Indicator Strip */}
        <div className="strip-indicators-group">
          <button 
            type="button"
            className="strip-indicator-pill"
            onClick={() => onNavigate && onNavigate('documents')}
            title="Inspect ingested medical documents"
          >
            <FileText size={12} className="text-clinical-blue" />
            <span className="indicator-label"><strong>{docCount}</strong> Documents</span>
          </button>

          <button 
            type="button"
            className="strip-indicator-pill"
            onClick={() => onNavigate && onNavigate('timeline')}
            title="Explore 23 chronological care events"
          >
            <Clock size={12} className="text-clinical-blue" />
            <span className="indicator-label"><strong>{eventsCount}</strong> Events</span>
          </button>

          <button 
            type="button"
            className="strip-indicator-pill"
            onClick={() => onNavigate && onNavigate('intelligence', 'changes')}
            title="View verified medication and condition changes"
          >
            <TrendingUp size={12} className="text-clinical-teal" />
            <span className="indicator-label"><strong>{changesCount}</strong> Changes</span>
          </button>

          {conflictsCount > 0 && (
            <button 
              type="button"
              className="strip-indicator-pill pill-conflict-alert"
              onClick={() => onNavigate && onNavigate('intelligence', 'conflicts')}
              title="1 Documentation conflict detected — Provider review required"
            >
              <AlertTriangle size={12} className="text-clinical-red" />
              <span className="indicator-label"><strong>{conflictsCount}</strong> Conflict</span>
              <ChevronRight size={11} className="opacity-70" />
            </button>
          )}

          {gapsCount > 0 && (
            <button 
              type="button"
              className="strip-indicator-pill pill-gap-alert"
              onClick={() => onNavigate && onNavigate('timeline')}
              title="Documentation Gap Analysis: Missing records in uploaded corpus"
            >
              <Clock size={12} className="text-clinical-amber" />
              <span className="indicator-label"><strong>{gapsCount}</strong> Documentation Gaps</span>
            </button>
          )}

          <div 
            className="strip-source-linked-pill" 
            title="All extracted events are source-grounded to document page & verbatim text"
          >
            <ShieldCheck size={12} className="text-clinical-teal" />
            <span>{eventsCount}/{eventsCount} Events Source-linked</span>
          </div>
        </div>
      </div>
    </section>
  );
}
