import React, { useState, useEffect } from 'react';
import { 
  GitBranch, 
  Clock, 
  FileText, 
  ExternalLink, 
  Activity, 
  Pill, 
  Stethoscope, 
  Scan, 
  LogOut,
  ChevronRight,
  Info
} from 'lucide-react';
import { getJourneyGraph } from '../services/api';

export default function PatientJourneyGraph({ 
  patientId, 
  onInspectDocument 
}) {
  const [graphData, setGraphData] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!patientId) return;
    setLoading(true);
    getJourneyGraph(patientId)
      .then((data) => {
        setGraphData(data);
        if (data.nodes && data.nodes.length > 0) {
          setSelectedNode(data.nodes[0]);
        }
      })
      .catch((err) => console.error('Failed to load journey graph:', err))
      .finally(() => setLoading(false));
  }, [patientId]);

  if (loading) {
    return (
      <div className="empty-journey-state">
        <GitBranch className="animate-spin text-cyan" size={36} />
        <p>Generating Patient Journey Graph...</p>
      </div>
    );
  }

  const nodes = graphData?.nodes || [];
  const edges = graphData?.edges || [];

  const getNodeIcon = (type) => {
    switch (type) {
      case 'test': return <Activity size={15} className="text-cyan" />;
      case 'medication': return <Pill size={15} className="text-emerald" />;
      case 'condition': return <Stethoscope size={15} className="text-purple" />;
      case 'procedure': return <Scan size={15} className="text-indigo" />;
      case 'discharge': return <LogOut size={15} className="text-rose" />;
      default: return <Clock size={15} className="text-blue" />;
    }
  };

  // Find incoming and outgoing edges for selected node
  const incomingEdges = selectedNode ? edges.filter(e => e.target === selectedNode.id) : [];
  const outgoingEdges = selectedNode ? edges.filter(e => e.source === selectedNode.id) : [];

  return (
    <div className="journey-container animate-fade-in">
      <div className="section-header">
        <div>
          <h2>Connected Patient Journey</h2>
          <p className="text-secondary">
            Visual sequence showing how lab findings led to specialist consultations, therapies, and clinical outcomes.
          </p>
        </div>
      </div>

      <div className="journey-layout">
        {/* Journey Flow Graph Cards */}
        <div className="journey-graph-card">
          <div className="journey-graph-header">
            <span className="flex items-center gap-2">
              <GitBranch size={16} className="text-cyan" />
              <strong>Care Progression Map ({nodes.length} Key Milestones)</strong>
            </span>
            <span className="text-xs text-muted">Click any milestone node to view details</span>
          </div>

          <div className="journey-nodes-track">
            {nodes.map((node, idx) => {
              const isSelected = selectedNode?.id === node.id;
              return (
                <div key={node.id} className="journey-node-wrapper">
                  <button
                    className={`journey-node-item ${isSelected ? 'selected' : ''} node-${node.event_type}`}
                    onClick={() => setSelectedNode(node)}
                  >
                    <div className="node-icon-bubble">
                      {getNodeIcon(node.event_type)}
                    </div>
                    <div className="node-content">
                      <div className="node-date-row">
                        <span className="node-date">{node.event_date}</span>
                        <span className="node-type-label">{node.event_type}</span>
                      </div>
                      <h4 className="node-title">{node.label}</h4>
                      <div className="node-source-pill">
                        <FileText size={11} />
                        <span>{node.document_name}</span>
                      </div>
                    </div>
                  </button>

                  {idx < nodes.length - 1 && (
                    <div className="journey-connector-arrow">
                      <ChevronRight size={18} className="text-muted" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Milestone Detail Inspector */}
        <div className="journey-inspector-panel">
          {selectedNode ? (
            <div className="inspector-content animate-fade-in">
              <div className="inspector-header">
                <span className="badge-pill badge-primary">{selectedNode.event_type.toUpperCase()}</span>
                <h3 className="inspector-title">{selectedNode.full_label}</h3>
                <span className="text-sm text-secondary">Occurred on: {selectedNode.event_date}</span>
              </div>

              {/* Evidence Quote */}
              <div className="inspector-evidence-box">
                <div className="text-xs text-cyan flex items-center gap-1 mb-1">
                  <FileText size={12} />
                  <span>Grounding Source Evidence:</span>
                </div>
                <blockquote className="text-sm italic text-primary">
                  "{selectedNode.supporting_text}"
                </blockquote>
                <div className="text-xs text-muted mt-2">
                  Document: <strong>{selectedNode.document_name}</strong>
                </div>
              </div>

              {/* Connections */}
              <div className="inspector-connections">
                <h4>
                  <GitBranch size={14} className="text-teal inline mr-1" />
                  Clinical Relationships:
                </h4>

                {incomingEdges.length > 0 && (
                  <div className="edge-group">
                    <span className="text-xs text-muted">Preceded By:</span>
                    {incomingEdges.map(e => {
                      const srcNode = nodes.find(n => n.id === e.source);
                      return (
                        <div key={e.id} className="edge-pill">
                          <span className="edge-type-tag">{e.label}</span>
                          <span>{srcNode?.label || 'Preceding Event'}</span>
                        </div>
                      );
                    })}
                  </div>
                )}

                {outgoingEdges.length > 0 && (
                  <div className="edge-group mt-2">
                    <span className="text-xs text-muted">Led To / Followed By:</span>
                    {outgoingEdges.map(e => {
                      const tgtNode = nodes.find(n => n.id === e.target);
                      return (
                        <div key={e.id} className="edge-pill">
                          <span className="edge-type-tag">{e.label}</span>
                          <span>{tgtNode?.label || 'Subsequent Event'}</span>
                        </div>
                      );
                    })}
                  </div>
                )}

                {incomingEdges.length === 0 && outgoingEdges.length === 0 && (
                  <p className="text-xs text-muted mt-1">Autonomous milestone without recorded direct dependencies.</p>
                )}
              </div>

              <div className="inspector-actions mt-4">
                <button 
                  className="btn btn-outline btn-full"
                  onClick={() => onInspectDocument(selectedNode.id, selectedNode.supporting_text)}
                >
                  <ExternalLink size={14} />
                  <span>Inspect Source Document</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="empty-inspector">
              <Info size={28} className="text-muted" />
              <p>Select any milestone node on the left to inspect clinical evidence.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
