import React, { useState, useRef } from 'react';
import { 
  UploadCloud, 
  FileText, 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  Eye, 
  Download, 
  RefreshCw,
  Plus
} from 'lucide-react';
import ProcessingPipeline from './ProcessingPipeline';


export default function DocumentUploader({ 
  patient, 
  documents, 
  onRefresh, 
  onViewDocument 
}) {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [processingDocId, setProcessingDocId] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files));
      setErrorMsg('');
    }
  };

  const handleUpload = async () => {
    if (!patient || selectedFiles.length === 0) return;
    setIsUploading(true);
    setErrorMsg('');

    try {
      await uploadDocuments(patient.patient_id, selectedFiles);
      setSelectedFiles([]);
      if (fileInputRef.current) fileInputRef.current.value = '';
      if (onRefresh) onRefresh();
    } catch (err) {
      setErrorMsg(err.message || 'Failed to upload documents.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleReprocess = async (docId) => {
    setProcessingDocId(docId);
    try {
      await processDocument(docId);
      if (onRefresh) onRefresh();
    } catch (err) {
      alert(`Processing error: ${err.message}`);
    } finally {
      setProcessingDocId(null);
    }
  };

  const formatDocType = (typeStr) => {
    const map = {
      lab_report: 'Lab Report',
      prescription: 'Prescription',
      clinical_note: 'Clinical Note',
      imaging_report: 'Imaging Report',
      discharge_summary: 'Discharge Summary',
    };
    return map[typeStr] || typeStr.replace('_', ' ');
  };

  const getDocBadgeClass = (typeStr) => {
    const map = {
      lab_report: 'badge-doc-lab',
      prescription: 'badge-doc-rx',
      clinical_note: 'badge-doc-note',
      imaging_report: 'badge-doc-imaging',
      discharge_summary: 'badge-doc-discharge',
    };
    return map[typeStr] || 'badge-doc-default';
  };

  return (
    <div className="uploader-container animate-fade-in">
      <div className="section-header">
        <div>
          <h2>Medical Document Intelligence</h2>
          <p className="text-secondary">
            Ingest heterogeneous records (PDFs, clinical notes, prescriptions, imaging scans).
          </p>
        </div>
      </div>

      {/* Processing Pipeline Stage Tracker */}
      <ProcessingPipeline 
        isProcessing={isUploading || !!processingDocId}
        currentStage={isUploading ? 'uploading' : (processingDocId ? 'event_extraction' : 'completed')}
      />

      {/* Drag & Drop Upload Zone */}
      <div className="upload-dropzone" onClick={() => fileInputRef.current?.click()}>
        <input 
          type="file" 
          ref={fileInputRef} 
          onChange={handleFileChange} 
          multiple 
          accept=".pdf,.txt,.png,.jpg,.jpeg"
          style={{ display: 'none' }}
        />
        <div className="dropzone-content">
          <UploadCloud className="dropzone-icon text-cyan" size={40} />
          <div className="dropzone-text">
            <h3>Drag & Drop Medical Documents</h3>
            <p>Supports Laboratory Reports, Prescriptions, Clinical Notes, Imaging, and Discharge Summaries</p>
            <span className="dropzone-formats">PDF, TXT, PNG, JPG (up to 20MB per document)</span>
          </div>
          <button className="btn btn-secondary mt-2" type="button">
            <Plus size={15} />
            <span>Browse Files</span>
          </button>
        </div>
      </div>

      {selectedFiles.length > 0 && (
        <div className="selected-files-bar animate-fade-in">
          <span><strong>{selectedFiles.length}</strong> file(s) selected: {selectedFiles.map(f => f.name).join(', ')}</span>
          <button className="btn btn-primary" onClick={handleUpload} disabled={isUploading}>
            {isUploading ? 'Extracting & Processing...' : 'Upload & Process Documents'}
          </button>
        </div>
      )}

      {errorMsg && (
        <div className="error-alert">
          <AlertCircle size={18} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Document Records Table */}
      <div className="doc-list-section">
        <div className="doc-list-header">
          <h3>Uploaded Medical Records ({documents?.length || 0})</h3>
          <button className="btn btn-ghost" onClick={onRefresh}>
            <RefreshCw size={14} />
            <span>Refresh</span>
          </button>
        </div>

        {documents && documents.length > 0 ? (
          <div className="documents-grid">
            {documents.map((doc) => (
              <div key={doc.document_id} className="document-card">
                <div className="document-card-top">
                  <div className="document-icon-wrapper">
                    <FileText size={20} className="text-cyan" />
                  </div>
                  <div className="document-info">
                    <h4 className="document-filename" title={doc.original_filename}>
                      {doc.original_filename}
                    </h4>
                    <span className={`badge-pill ${getDocBadgeClass(doc.document_type)}`}>
                      {formatDocType(doc.document_type)}
                    </span>
                  </div>
                </div>

                <div className="document-meta-row">
                  <span>Pages: {doc.page_count}</span>
                  <span>Size: {(doc.file_size / 1024).toFixed(1)} KB</span>
                  <span>Date: {doc.document_date || 'Undated'}</span>
                </div>

                <div className="document-status-row">
                  {doc.processing_status === 'completed' ? (
                    <span className="status-indicator status-success">
                      <CheckCircle2 size={14} />
                      <span>Extracted & Indexed</span>
                    </span>
                  ) : doc.processing_status === 'processing' ? (
                    <span className="status-indicator status-working">
                      <Clock size={14} />
                      <span>Processing ({doc.processing_stage})</span>
                    </span>
                  ) : (
                    <span className="status-indicator status-failed">
                      <AlertCircle size={14} />
                      <span>Failed</span>
                    </span>
                  )}
                </div>

                <div className="document-card-actions">
                  <button 
                    className="btn-card-action"
                    onClick={() => onViewDocument(doc.document_id)}
                    title="Inspect document text and highlighted evidence"
                  >
                    <Eye size={14} />
                    <span>View Text</span>
                  </button>

                  <a 
                    href={getDocumentDownloadUrl(doc.document_id)} 
                    target="_blank" 
                    rel="noreferrer" 
                    className="btn-card-action"
                    title="Open original document"
                  >
                    <Download size={14} />
                    <span>Open PDF</span>
                  </a>

                  <button 
                    className="btn-card-action btn-card-reprocess"
                    onClick={() => handleReprocess(doc.document_id)}
                    disabled={processingDocId === doc.document_id}
                    title="Re-run AI extraction"
                  >
                    <RefreshCw size={13} className={processingDocId === doc.document_id ? 'animate-spin' : ''} />
                    <span>Re-parse</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-docs-box">
            <p>No documents uploaded yet. Drag and drop files above or click "Load Demo Patient" to seed 5 sample documents.</p>
          </div>
        )}
      </div>
    </div>
  );
}
