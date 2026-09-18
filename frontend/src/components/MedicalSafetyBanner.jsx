import React, { useState } from 'react';
import { ShieldAlert, X } from 'lucide-react';

export default function MedicalSafetyBanner() {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <aside className="compact-safety-strip" role="alert" aria-label="Medical safety notice">
      <div className="safety-strip-inner">
        <ShieldAlert size={13} className="safety-strip-icon flex-shrink-0" />
        <span className="safety-strip-text">
          <strong>Medical Safety Notice:</strong> Demonstration & document intelligence only. Not medical advice or diagnosis. Synthetic patient dataset (Sarah Jenkins).
        </span>
      </div>
      <button 
        type="button"
        className="safety-strip-dismiss" 
        onClick={() => setDismissed(true)} 
        aria-label="Dismiss safety notice"
      >
        <X size={12} />
      </button>
    </aside>
  );
}
