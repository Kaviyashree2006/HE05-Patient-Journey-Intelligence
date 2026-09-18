import React, { useState } from 'react';
import { 
  Send, 
  FileText, 
  ExternalLink, 
  AlertCircle, 
  CheckCircle2, 
  ShieldCheck, 
  Search,
  BookOpen,
  Terminal,
  Activity
} from 'lucide-react';
import { askQuestion } from '../services/api';

export default function EvidenceQA({ 
  patient, 
  onInspectDocument 
}) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: 'Clinical Record Investigation Engine active. Formulate clinical inquiries regarding documented diagnoses, pharmacotherapy transitions, laboratory findings, or contradictory statements across Sarah Jenkins\' medical record corpus. All responses are derived strictly from primary document text with explicit citations.',
      citations: []
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);

  // Exact suggested questions from user prompt
  const suggestedQuestions = [
    "What changed over the documented record?",
    "Which medications changed?",
    "What documentation conflicts exist?",
    "What documentation gaps were detected?"
  ];

  const handleSend = async (qText) => {
    const query = qText || inputText;
    if (!query.trim() || !patient || loading) return;

    const userMsg = { role: 'user', text: query, citations: [] };
    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setLoading(true);

    try {
      const resp = await askQuestion(patient.patient_id, query);
      const botMsg = {
        role: 'assistant',
        text: resp.answer,
        hasEvidence: resp.has_sufficient_evidence,
        citations: resp.citations || []
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: `Error retrieving evidence: ${err.message}`,
          isError: true,
          citations: []
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="clinical-investigation-workspace animate-fade-in">
      {/* Header */}
      <div className="investigation-header-bar">
        <div className="investigation-header-left">
          <div className="investigation-kicker font-mono">PRIMARY RECORD RETRIEVAL</div>
          <h2 className="investigation-title">CLINICAL RECORD INVESTIGATION</h2>
          <p className="investigation-sub">
            Formulate natural language clinical inquiries verified strictly against uploaded medical records with verbatim citations.
          </p>
        </div>

        <div className="investigation-status-badge">
          <ShieldCheck size={14} className="text-clinical-teal" />
          <span>Evidence-grounded engine</span>
        </div>
      </div>

      {/* Suggested Clinical Inquiries Bar */}
      <div className="suggested-queries-shelf">
        <span className="queries-shelf-label">Suggested Clinical Inquiries:</span>
        <div className="queries-shelf-chips">
          {suggestedQuestions.map((q, i) => (
            <button
              key={i}
              type="button"
              className="clinical-query-chip"
              onClick={() => handleSend(q)}
              disabled={loading}
            >
              <Search size={11} className="chip-search-icon" />
              <span>"{q}"</span>
            </button>
          ))}
        </div>
      </div>

      {/* Structured Investigation Log (NOT a consumer chat bubble layout) */}
      <div className="investigation-entries-log">
        {messages.map((msg, index) => (
          <div key={index} className={`investigation-entry-block entry-${msg.role} animate-fade-in`}>
            {msg.role === 'user' ? (
              <div className="user-query-container">
                <div className="query-lead-tag font-mono">CLINICAL INQUIRY:</div>
                <div className="query-text-body">{msg.text}</div>
              </div>
            ) : (
              <div className="finding-result-container">
                <div className="finding-header-row">
                  <div className="finding-badge-group font-mono">
                    <Activity size={13} className="text-clinical-teal" />
                    <span>EVIDENCED CLINICAL FINDING</span>
                  </div>
                  {msg.hasEvidence === false && (
                    <span className="unsupported-evidence-tag font-mono">CORPUS EVIDENCE INSUFFICIENT</span>
                  )}
                </div>

                <div className="finding-text-body">
                  {msg.text}
                </div>

                {/* Evidence Citations Strip Underneath Answer */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="citations-evidence-tray">
                    <div className="tray-title-row">
                      <CheckCircle2 size={13} className="text-clinical-teal" />
                      <span className="tray-title font-mono">PRIMARY SOURCE CITATIONS ({msg.citations.length})</span>
                    </div>

                    <div className="tray-citations-grid">
                      {msg.citations.map((cite, cIdx) => (
                        <div key={cIdx} className="citation-evidence-card">
                          <div className="citation-card-top">
                            <div className="citation-doc-info">
                              <FileText size={12} className="text-clinical-blue" />
                              <strong className="doc-title-text">{cite.document_name}</strong>
                              <span className="doc-page-meta font-mono">Page {cite.page || 1} • {cite.event_date || 'Encounter'}</span>
                            </div>

                            <button 
                              type="button"
                              className="btn-open-source-drawer"
                              onClick={() => onInspectDocument && onInspectDocument(cite.document_id, cite.supporting_text)}
                              title="Open exact cited document in Evidence Drawer"
                            >
                              <ExternalLink size={11} />
                              <span>Inspect Source</span>
                            </button>
                          </div>

                          <blockquote className="citation-exact-quote">
                            "{cite.supporting_text}"
                          </blockquote>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="investigation-loading-block animate-fade-in">
            <Activity size={16} className="animate-spin text-clinical-blue" />
            <span className="loading-text font-mono">Retrieving primary document citations and corroborating clinical facts...</span>
          </div>
        )}
      </div>

      {/* Query Input Bar */}
      <form 
        className="investigation-input-strip"
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
      >
        <div className="input-field-wrapper">
          <Search size={15} className="input-search-glyph" />
          <input 
            type="text"
            placeholder="Enter clinical question regarding Sarah Jenkins' trajectory (e.g. 'Which medications changed?')..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            className="clinical-search-input"
            disabled={loading}
          />
        </div>
        <button 
          type="submit" 
          className="btn btn-primary investigation-submit-btn"
          disabled={!inputText.trim() || loading}
        >
          <Send size={13} />
          <span>Execute Inquiry</span>
        </button>
      </form>
    </div>
  );
}
