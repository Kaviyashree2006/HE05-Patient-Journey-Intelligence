import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Download, 
  Search, 
  CheckCircle2, 
  ExternalLink,
  Highlighter,
  Eye,
  Info
} from 'lucide-react';
import { getDocument, getDocumentDownloadUrl } from '../services/api';

export default function DocumentViewer({ 
  documents, 
  initialDocId, 
  highlightSnippet 
}) {
  const [selectedDocId, setSelectedDocId] = useState(initialDocId || (documents?.[0]?.document_id));
  const [docDetail, setDocDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (initialDocId) {
      setSelectedDocId(initialDocId);
    } else if (documents && documents.length > 0 && !selectedDocId) {
      setSelectedDocId(documents[0].document_id);
    }
  }, [initialDocId, documents]);

  useEffect(() => {
    if (!selectedDocId) return;
    setLoading(true);
    getDocument(selectedDocId)
      .then((data) => setDocDetail(data))
      .catch((err) => console.error('Failed to load document:', err))
      .finally(() => setLoading(false));
  }, [selectedDocId]);

  const activeSnippet = highlightSnippet || searchQuery;

  const renderHighlightedText = (text) => {
    if (!text) return <p className="text-muted">No text content available.</p>;
    if (!activeSnippet) return <pre className="doc-raw-text">{text}</pre>;

    const regex = new RegExp(`(${activeSnippet.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = text.split(regex);

    return (
      <pre className="doc-raw-text">
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
  };

  return (
    <div className="viewer-container animate-fade-in">
      <div className="section-header">
        <div>
          <h2>Source Document Inspector & Grounding Viewer</h2>
          <p className="text-secondary">
            Inspect the original medical source records and verify evidence quotes directly against source text.
          </p>
        </div>
      </div>

      <div className="viewer-layout">
        {/* Document Selector Sidebar */}
        <div className="viewer-sidebar">
          <div className="sidebar-header">
            <h4>Available Documents ({documents?.length || 0})</h4>
          </div>
          <div className="sidebar-list">
            {documents?.map((doc) => {
              const isSelected = selectedDocId === doc.document_id;
              return (
                <button
                  key={doc.document_id}
                  className={`sidebar-doc-item ${isSelected ? 'selected' : ''}`}
                  onClick={() => setSelectedDocId(doc.document_id)}
                >
                  <FileText size={16} className={isSelected ? 'text-cyan' : 'text-muted'} />
                  <div className="sidebar-doc-info">
                    <span className="sidebar-doc-name" title={doc.original_filename}>
                      {doc.original_filename}
                    </span>
                    <span className="sidebar-doc-type">
                      {doc.document_type.replace('_', ' ')} • {doc.document_date || 'Undated'}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Document Content Panel */}
        <div className="viewer-main-panel">
          {docDetail ? (
            <div className="viewer-content">
              {/* Document Meta Header */}
              <div className="viewer-content-header">
                <div>
                  <h3 className="viewer-filename">{docDetail.original_filename}</h3>
                  <div className="viewer-tags-row">
                    <span className="badge-pill badge-primary">Type: {docDetail.document_type.replace('_', ' ')}</span>
                    <span className="text-xs text-muted">Authored: {docDetail.document_date || 'Undated'}</span>
                    <span className="text-xs text-muted">Pages: {docDetail.page_count}</span>
                    <span className="text-xs text-muted">Size: {(docDetail.file_size / 1024).toFixed(1)} KB</span>
                  </div>
                </div>

                <div className="viewer-actions-cluster">
                  <a 
                    href={getDocumentDownloadUrl(docDetail.document_id)}
                    target="_blank"
                    rel="noreferrer"
                    className="btn btn-outline"
                    title="Open / Download original PDF document"
                  >
                    <Download size={14} />
                    <span>Open Native PDF</span>
                  </a>
                </div>
              </div>

              {/* Highlight Banner if active */}
              {highlightSnippet && (
                <div className="snippet-active-banner animate-fade-in">
                  <Highlighter size={16} className="text-amber flex-shrink-0" />
                  <div className="snippet-active-text">
                    <strong>Evidence Snippet Active:</strong> Highlighting cited supporting quote in document text below:
                    <div className="snippet-active-quote">"{highlightSnippet}"</div>
                  </div>
                </div>
              )}

              {/* Search Bar within Document */}
              <div className="viewer-search-bar">
                <Search size={15} className="text-muted" />
                <input 
                  type="text"
                  placeholder="Search inside this document..."
                  value={searchQuery}
                  onChange={(e) => setSearchTerm ? setSearchQuery(e.target.value) : setSearchQuery(e.target.value)}
                  className="viewer-search-input"
                />
                {searchQuery && (
                  <button className="btn-clear-search" onClick={() => setSearchQuery('')}>Clear</button>
                )}
              </div>

              {/* Document Text Viewport */}
              <div className="viewer-viewport">
                {loading ? (
                  <div className="viewer-loading">Loading document text...</div>
                ) : (
                  renderHighlightedText(docDetail.extracted_text)
                )}
              </div>
            </div>
          ) : (
            <div className="empty-viewer-state">
              <Eye size={36} className="text-muted" />
              <p>Select a document from the left sidebar to view contents.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
