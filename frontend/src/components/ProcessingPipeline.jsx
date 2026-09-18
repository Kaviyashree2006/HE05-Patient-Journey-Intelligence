import React from 'react';
import { 
  UploadCloud, 
  FileText, 
  BrainCircuit, 
  Stethoscope, 
  GitMerge, 
  CheckCircle2, 
  Loader2,
  ArrowRight
} from 'lucide-react';

export default function ProcessingPipeline({ currentStage = 'completed', isProcessing = false }) {
  const stages = [
    { id: 'uploading', label: 'UPLOAD', icon: UploadCloud, desc: 'Corpus ingestion' },
    { id: 'text_extraction', label: 'TEXT EXTRACTION', icon: FileText, desc: 'Native digital PDF parsing' },
    { id: 'ai_understanding', label: 'DOCUMENT UNDERSTANDING', icon: BrainCircuit, desc: 'Clinical classification' },
    { id: 'event_extraction', label: 'EVENT EXTRACTION', icon: Stethoscope, desc: 'Structured entity parsing' },
    { id: 'relationship_processing', label: 'TEMPORAL REASONING', icon: GitMerge, desc: 'Causal & trajectory links' },
    { id: 'timeline_generation', label: 'TIMELINE GENERATION', icon: CheckCircle2, desc: 'Evidence-grounded journey' },
  ];

  const stageOrder = stages.map(s => s.id);
  const currentIdx = currentStage === 'completed' 
    ? stages.length 
    : stageOrder.indexOf(currentStage);

  return (
    <div className="connected-pipeline-flow-card">
      <div className="pipeline-flow-header">
        <div className="flow-title-group">
          <span className="flow-kicker">DOCUMENT INTELLIGENCE PIPELINE</span>
          <h3 className="flow-heading">Deterministic Multi-Document Extraction & Synthesis</h3>
        </div>
        <span className="pipeline-status-badge">
          {currentStage === 'completed' ? (
            <span className="text-clinical-teal flex items-center gap-1">
              <CheckCircle2 size={13} />
              <span>Pipeline Active & Grounded</span>
            </span>
          ) : (
            <span className="text-clinical-blue flex items-center gap-1">
              <Loader2 size={13} className="animate-spin" />
              <span>Running: {currentStage.replace('_', ' ').toUpperCase()}</span>
            </span>
          )}
        </span>
      </div>

      {/* Connected Flow Steps */}
      <div className="pipeline-connected-steps">
        {stages.map((stage, idx) => {
          const Icon = stage.icon;
          const isDone = currentIdx > idx || currentStage === 'completed';
          const isCurrent = currentIdx === idx && isProcessing;

          return (
            <React.Fragment key={stage.id}>
              <div 
                className={`pipeline-flow-step ${isDone ? 'step-completed' : ''} ${isCurrent ? 'step-active' : ''}`}
              >
                <div className="flow-step-number">{idx + 1}</div>
                <div className="flow-step-icon-wrap">
                  {isCurrent ? (
                    <Loader2 size={16} className="animate-spin text-clinical-blue" />
                  ) : (
                    <Icon size={16} />
                  )}
                </div>
                <div className="flow-step-text">
                  <strong className="flow-step-title">{stage.label}</strong>
                  <span className="flow-step-sub">{stage.desc}</span>
                </div>
              </div>

              {idx < stages.length - 1 && (
                <div className={`pipeline-step-connector ${isDone ? 'connector-done' : ''}`} aria-hidden="true">
                  <ArrowRight size={14} className="connector-arrow-icon" />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
