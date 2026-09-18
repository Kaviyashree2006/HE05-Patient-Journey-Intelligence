import React, { useState, useEffect, useRef } from 'react';
import { 
  X, 
  FileText, 
  Download, 
  Search, 
  Highlighter, 
  ExternalLink,
  ShieldCheck,
  Calendar,
  Layers,
  ChevronRight
} from 'lucide-react';
import { getDocument, getDocumentDownloadUrl } from '../services/api';

export default function EvidenceDrawer({ 
  isOpen, 
  onClose, 
  documents, 
  initialDocId, 
  highlightSnippet 
}) {
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [docDetail, setDocDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const textContainerRef = useRef(null);

  useEffect(() => {
    if (initialDocId) {
      setSelectedDocId(initialDocId);
    } else if (documents && documents.length > 0 && !selectedDocId) {
      setSelectedDocId(documents[0].document_id);
    }
  }, [initialDocId, documents, isOpen]);

  useEffect(() => {
    if (!selectedDocId || !isOpen) return;
    setLoading(true);
    getDocument(selectedDocId)
      .then((data) => setDocDetail(data))
      .catch((err) => console.error('Failed to load document text:', err))
      .finally(() => setLoading(false));
  }, [selectedDocId, isOpen]);

  // Scroll to highlighted snippet when loaded
  useEffect(() => {
    if (docDetail && highlightSnippet && textContainerRef.current) {
      setTimeout(() => {
        const mark = textContainerRef.current?.querySelector('mark');
        if (mark) {
          mark.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 150);
    }
  }, [docDetail, highlightSnippet]);

  // Close drawer on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const activeSnippet = highlightSnippet || searchQuery;

  const renderHighlightedText = (text) => {
    if (!text) return <p className="text-muted p-4">No extracted text content available.</p>;
    if (!activeSnippet) return <pre className="drawer-doc-raw-text">{text}</pre>;

    const cleanSnippet = activeSnippet.trim();
    if (!cleanSnippet) return <pre className="drawer-doc-raw-text">{text}</pre>;

    try {
      const escaped = cleanSnippet.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const regex = new RegExp(`(${escaped})`, 'gi');
      const parts = text.split(regex);

      return (
        <pre className="drawer-doc-raw-text">
          {parts.map((part, i) => 
            regex.test(part) ? (
              <mark key={i} className="evidence-text-highlight">
                {part}
              </mark>
            ) : (
              part
            )
          )}
        </pre>
      );
    } catch {
      return <pre className="drawer-doc-raw-text">{text}</pre>;
    }
  };

  return (
    <div className="drawer-backdrop animate-fade-in" onClick={onClose}>
      <div 
        className="drawer-panel evidence-drawer animate-slide-left" 
        onClick={(e) => e.stopPropagation()}
      >
        {/* Drawer Header */}
        <div className="drawer-header">
          <div className="drawer-header-titles">
            <div className="flex items-center gap-2">
              <FileText size={18} className="text-cyan" />
              <h3 className="drawer-title">Source Record Inspector</h3>
            </div>
            <p className="drawer-subtitle">
              Verbatim primary record evidence grounding with highlighted passage verification.
            </p>
          </div>
          <button 
            className="drawer-close-btn" 
            onClick={onClose} 
            title="Close inspector (Esc)"
          >
            <X size={20} />
          </button>
        </div>

        {/* Available Documents Selector Bar */}
        {documents && documents.length > 1 && (
          <div className="drawer-doc-tabs">
            {documents.map((doc) => {
              const isSelected = selectedDocId === doc.document_id;
              return (
                <button
                  key={doc.document_id}
                  className={`drawer-doc-tab ${isSelected ? 'active' : ''}`}
                  onClick={() => setSelectedDocId(doc.document_id)}
                  title={doc.original_filename}
                >
                  <FileText size={13} className={isSelected ? 'text-cyan' : 'text-muted'} />
                  <span>{doc.original_filename}</span>
                </button>
              );
            })}
          </div>
        )}

        {/* Document Details & Quick Actions */}
        {docDetail && (
          <div className="drawer-doc-meta">
            <div className="drawer-meta-info">
              <span className="badge-pill badge-primary">
                {docDetail.document_type?.replace('_', ' ').toUpperCase() || 'MEDICAL RECORD'}
              </span>
              <span className="text-xs text-muted">
                Authored: <strong>{docDetail.document_date || 'Undated'}</strong>
              </span>
              <span className="text-xs text-muted">
                Pages: <strong>{docDetail.page_count || 1}</strong>
              </span>
            </div>

            <a 
              href={getDocumentDownloadUrl(docDetail.document_id)}
              target="_blank"
              rel="noreferrer"
              className="btn btn-sm btn-outline"
              title="Open or download original PDF"
            >
              <Download size={13} />
              <span>Native PDF</span>
            </a>
          </div>
        )}

        {/* Active Grounding Snippet Callout */}
        {highlightSnippet && (
          <div className="drawer-snippet-callout">
            <div className="drawer-snippet-header">
              <Highlighter size={14} className="text-amber flex-shrink-0" />
              <span>Cited Grounding Passage (Highlighted Below):</span>
            </div>
            <blockquote className="drawer-snippet-quote">
              "{highlightSnippet}"
            </blockquote>
          </div>
        )}

        {/* Search inside Document Text */}
        <div className="drawer-search-bar">
          <Search size={14} className="text-muted" />
          <input 
            type="text"
            placeholder="Search within this document..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="drawer-search-input"
          />
          {searchQuery && (
            <button className="btn-clear-search" onClick={() => setSearchQuery('')}>
              <X size={13} />
            </button>
          )}
        </div>

        {/* Document Text Body */}
        <div className="drawer-body" ref={textContainerRef}>
          {loading ? (
            <div className="drawer-loading">
              <FileText className="animate-spin text-cyan" size={28} />
              <p>Loading document text...</p>
            </div>
          ) : (
            renderHighlightedText(docDetail?.extracted_text)
          )}
        </div>

        {/* Drawer Footer */}
        <div className="drawer-footer">
          <div className="flex items-center gap-2 text-xs text-secondary">
            <ShieldCheck size={14} className="text-teal" />
            <span>HE-05 Strict Source Traceability Engine Active</span>
          </div>
          <button className="btn btn-sm btn-secondary" onClick={onClose}>
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
}
