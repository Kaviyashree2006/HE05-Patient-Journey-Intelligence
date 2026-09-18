import React from 'react';
import { 
  Activity, 
  Sparkles,
  UserCheck,
  ShieldCheck,
  Menu,
  X
} from 'lucide-react';

export default function Navbar({ 
  patients, 
  selectedPatient, 
  onSelectPatient, 
  onSeedDemo,
  isSeeding,
  onToggleMobileNav,
  isMobileNavOpen
}) {
  return (
    <header className="clinical-top-bar" role="banner">
      <div className="top-bar-inner">
        {/* Left: Mobile Toggle & Brand Application Identifier */}
        <div className="top-bar-left">
          <button 
            className="mobile-nav-toggle md:hidden"
            onClick={onToggleMobileNav}
            aria-label="Toggle navigation menu"
          >
            {isMobileNavOpen ? <X size={20} /> : <Menu size={20} />}
          </button>

          <div className="top-bar-brand">
            {/* EKG / Medical Waveform Icon */}
            <div className="brand-waveform-icon" aria-hidden="true">
              <Activity size={20} className="waveform-svg" />
            </div>

            <div className="brand-text-column">
              <div className="brand-title-line">
                <span className="brand-primary-text">EVIDENCE-LINKED</span>
                <span className="brand-secondary-text">PATIENT JOURNEY</span>
              </div>
              <div className="brand-sub-meta">
                <span className="brand-he-badge">HE-05</span>
                <span className="brand-meta-bullet">•</span>
                <span className="brand-system-role">Document Intelligence</span>
              </div>
            </div>
          </div>
        </div>

        {/* Center / Right: Patient Selector & Evidence Status */}
        <div className="top-bar-right">
          {patients && patients.length > 0 && (
            <div className="top-bar-patient-selector" title="Active Patient Profile">
              <div className="selector-lead-icon">
                <UserCheck size={14} />
              </div>
              <div className="selector-select-wrap">
                <select 
                  className="patient-select-control font-mono"
                  value={selectedPatient?.patient_id || ''}
                  onChange={(e) => {
                    const p = patients.find(x => x.patient_id === e.target.value);
                    if (p) onSelectPatient(p);
                  }}
                  aria-label="Select active patient"
                >
                  {patients.map(p => (
                    <option key={p.patient_id} value={p.patient_id}>
                      {p.name} — {p.patient_reference}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}

          <button 
            className="btn btn-topbar-demo"
            onClick={onSeedDemo}
            disabled={isSeeding}
            title="Load Sarah Jenkins (54F) longitudinal synthetic dataset"
          >
            <Sparkles size={13} className={isSeeding ? 'animate-spin' : ''} />
            <span>{isSeeding ? 'Loading Demo...' : 'Load Demo Patient'}</span>
          </button>

          {/* Evidence-grounded status */}
          <div className="evidence-grounded-status-badge" title="All extractions ground to verbatim primary document text">
            <ShieldCheck size={14} className="status-badge-icon" />
            <span className="status-badge-text">Evidence-grounded</span>
          </div>
        </div>
      </div>
    </header>
  );
}
