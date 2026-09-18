import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import MedicalSafetyBanner from './components/MedicalSafetyBanner';
import GlobalPatientHeader from './components/GlobalPatientHeader';
import DashboardView from './components/DashboardView';
import TimelineView from './components/TimelineView';
import ChangesConflictsView from './components/ChangesConflictsView';
import DocumentsEvidenceView from './components/DocumentsEvidenceView';
import EventInspectionDrawer from './components/EventInspectionDrawer';
import EvidenceDrawer from './components/EvidenceDrawer';
import { 
  getPatients, 
  seedDemoPatient, 
  getPatientDocuments, 
  getTimeline, 
  getIntelligenceSummary 
} from './services/api';
import './App.css';

export default function App() {
  // Core 4-Pillar Information Architecture Tabs:
  // 'overview', 'timeline', 'intelligence', 'documents'
  const [activeTab, setActiveTab] = useState('overview');
  const [intelligenceSubTab, setIntelligenceSubTab] = useState('changes');
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);

  // Patient & Clinical Data
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [timelineData, setTimelineData] = useState(null);
  const [summary, setSummary] = useState(null);
  const [isSeeding, setIsSeeding] = useState(false);
  const [loading, setLoading] = useState(true);

  // Contextual Drawers State
  const [inspectedEvent, setInspectedEvent] = useState(null);
  const [evidenceDrawerState, setEvidenceDrawerState] = useState({
    isOpen: false,
    docId: null,
    highlightSnippet: null
  });

  // Load all patient data
  const loadPatientData = useCallback(async (patientId) => {
    if (!patientId) return;
    try {
      const [docs, tl, summ] = await Promise.all([
        getPatientDocuments(patientId),
        getTimeline(patientId),
        getIntelligenceSummary(patientId),
      ]);
      setDocuments(docs);
      setTimelineData(tl);
      setSummary(summ);
    } catch (err) {
      console.error('Failed to load patient details:', err);
    }
  }, []);

  // Fetch initial patient list
  const refreshPatients = useCallback(async () => {
    try {
      const list = await getPatients();
      setPatients(list);
      if (list.length > 0) {
        setSelectedPatient((prev) => {
          const match = prev ? list.find((p) => p.patient_id === prev.patient_id) : null;
          return match || list[0];
        });
      } else {
        handleSeedDemo();
      }
    } catch (err) {
      console.error('Error fetching patients:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshPatients();
  }, [refreshPatients]);

  useEffect(() => {
    if (selectedPatient) {
      loadPatientData(selectedPatient.patient_id);
    }
  }, [selectedPatient, loadPatientData]);

  // Handle 1-Click Demo Seeding
  const handleSeedDemo = async () => {
    setIsSeeding(true);
    try {
      const seeded = await seedDemoPatient();
      await refreshPatients();
      setSelectedPatient(seeded);
      await loadPatientData(seeded.patient_id);
      setActiveTab('overview');
    } catch (err) {
      alert(`Demo seeding error: ${err.message}`);
    } finally {
      setIsSeeding(false);
    }
  };

  // Inspect document from any component (timeline, conflict, Q&A, drawer)
  const handleInspectDocument = (docId, snippet) => {
    const matchedDoc = documents?.find((d) => d.document_id === docId);
    const resolvedDocId = matchedDoc ? matchedDoc.document_id : (documents?.[0]?.document_id || null);
    setEvidenceDrawerState({
      isOpen: true,
      docId: resolvedDocId,
      highlightSnippet: snippet || null
    });
  };

  // Close evidence drawer
  const handleCloseEvidenceDrawer = () => {
    setEvidenceDrawerState({
      isOpen: false,
      docId: null,
      highlightSnippet: null
    });
  };

  // Coherent navigation handler
  const handleNavigate = (tab, subTab = null) => {
    setActiveTab(tab);
    setIsMobileNavOpen(false);
    if (subTab && tab === 'intelligence') {
      setIntelligenceSubTab(subTab);
    }
  };

  return (
    <div className="clinical-app-shell">
      {/* Top Clinical Header Bar */}
      <Navbar 
        patients={patients}
        selectedPatient={selectedPatient}
        onSelectPatient={(p) => setSelectedPatient(p)}
        onSeedDemo={handleSeedDemo}
        isSeeding={isSeeding}
        onToggleMobileNav={() => setIsMobileNavOpen(!isMobileNavOpen)}
        isMobileNavOpen={isMobileNavOpen}
      />

      {/* Top Medical Safety Notice */}
      <MedicalSafetyBanner />

      {/* Clinical Workspace: Left Sidebar + Main Content Viewport */}
      <div className="clinical-workspace-layout">
        {/* Left Navigation Sidebar */}
        <div className={`clinical-sidebar-wrapper ${isMobileNavOpen ? 'mobile-drawer-open' : ''}`}>
          <Sidebar 
            activeTab={activeTab}
            setActiveTab={(tab) => {
              setActiveTab(tab);
              setIsMobileNavOpen(false);
            }}
            summary={summary}
            timelineData={timelineData}
            documents={documents}
          />
        </div>

        {/* Backdrop for Mobile Sidebar Drawer */}
        {isMobileNavOpen && (
          <div 
            className="mobile-sidebar-backdrop"
            onClick={() => setIsMobileNavOpen(false)}
          />
        )}

        {/* Right Main Content Viewport */}
        <div className="clinical-main-viewport">
          {/* Global Persistent Patient Context Header */}
          {selectedPatient && (
            <GlobalPatientHeader 
              patient={selectedPatient}
              summary={summary}
              timeline={timelineData}
              onNavigate={handleNavigate}
            />
          )}

          {/* Active Clinical Pillar Content */}
          <main className="clinical-content-area">
            {/* PILLAR 1: OVERVIEW */}
            {activeTab === 'overview' && (
              <DashboardView 
                patient={selectedPatient}
                summary={summary}
                timeline={timelineData}
                onNavigate={handleNavigate}
                onInspectDocument={handleInspectDocument}
                onSelectEvent={(ev) => setInspectedEvent(ev)}
                onSeedDemo={handleSeedDemo}
                isSeeding={isSeeding}
              />
            )}

            {/* PILLAR 2: TIMELINE & JOURNEY */}
            {activeTab === 'timeline' && (
              <TimelineView 
                timelineData={timelineData}
                summary={summary}
                patientId={selectedPatient?.patient_id}
                onSelectEvent={(ev) => setInspectedEvent(ev)}
                onInspectDocument={handleInspectDocument}
              />
            )}

            {/* PILLAR 3: CLINICAL INTELLIGENCE */}
            {activeTab === 'intelligence' && (
              <ChangesConflictsView 
                summary={summary}
                patientId={selectedPatient?.patient_id}
                initialSubTab={intelligenceSubTab}
                onRefreshSummary={() => loadPatientData(selectedPatient?.patient_id)}
                onInspectDocument={handleInspectDocument}
              />
            )}

            {/* PILLAR 4: DOCUMENTS & EVIDENCE */}
            {activeTab === 'documents' && (
              <DocumentsEvidenceView 
                patient={selectedPatient}
                documents={documents}
                onRefresh={() => loadPatientData(selectedPatient?.patient_id)}
                onInspectDocument={handleInspectDocument}
              />
            )}
          </main>
        </div>
      </div>

      {/* Contextual Event Inspection Drawer (Non-blocking) */}
      <EventInspectionDrawer 
        event={inspectedEvent}
        isOpen={!!inspectedEvent}
        onClose={() => setInspectedEvent(null)}
        onInspectDocument={handleInspectDocument}
      />

      {/* Contextual Evidence Drawer (Slide-out Source Record Grounding) */}
      <EvidenceDrawer 
        isOpen={evidenceDrawerState.isOpen}
        onClose={handleCloseEvidenceDrawer}
        documents={documents}
        initialDocId={evidenceDrawerState.docId}
        highlightSnippet={evidenceDrawerState.highlightSnippet}
      />
    </div>
  );
}

