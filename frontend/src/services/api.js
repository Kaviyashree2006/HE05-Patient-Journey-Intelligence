const BASE_URL = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '');

export async function fetchJson(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) {
    let errorDetail = res.statusText;
    try {
      const data = await res.json();
      errorDetail = data.detail || data.error || errorDetail;
    } catch { }
    throw new Error(errorDetail || `Request failed with status ${res.status}`);
  }
  return res.json();
}

export async function getPatients() {
  return fetchJson(`${BASE_URL}/patients`);
}
export async function getPatient(patientId) {
  return fetchJson(`${BASE_URL}/patients/${patientId}`);
}
export async function createPatient(data) {
  return fetchJson(`${BASE_URL}/patients`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}
export async function seedDemoPatient() {
  return fetchJson(`${BASE_URL}/patients/seed-demo`, { method: 'POST' });
}
export async function getPatientDocuments(patientId) {
  return fetchJson(`${BASE_URL}/patients/${patientId}/documents`);
}
export async function getDocument(documentId) {
  return fetchJson(`${BASE_URL}/documents/${documentId}`);
}
export function getDocumentDownloadUrl(documentId) {
  return `${BASE_URL}/documents/${documentId}/file`;
}
export const getDocumentViewUrl = getDocumentDownloadUrl;
export async function uploadDocuments(patientId, files) {
  const formData = new FormData();
  for (const file of files) formData.append('files', file);
  return fetchJson(`${BASE_URL}/patients/${patientId}/documents?auto_process=true`, {
    method: 'POST',
    body: formData,
  });
}
export async function processDocument(documentId) {
  return fetchJson(`${BASE_URL}/documents/${documentId}/process`, { method: 'POST' });
}
export async function getTimeline(patientId, filters = {}) {
  const query = new URLSearchParams();
  if (filters.event_type) query.append('event_type', filters.event_type);
  if (filters.certainty) query.append('certainty', filters.certainty);
  if (filters.priority) query.append('priority', filters.priority);
  if (filters.evidence_level) query.append('evidence_level', filters.evidence_level);
  if (filters.search) query.append('search', filters.search);
  const qs = query.toString() ? `?${query.toString()}` : '';
  return fetchJson(`${BASE_URL}/patients/${patientId}/timeline${qs}`);
}
export async function getEventDetail(eventId) {
  return fetchJson(`${BASE_URL}/events/${eventId}`);
}
export async function getIntelligenceSummary(patientId) {
  return fetchJson(`${BASE_URL}/patients/${patientId}/summary`);
}
export async function getRelationships(patientId) {
  return fetchJson(`${BASE_URL}/patients/${patientId}/relationships`);
}
export async function getChanges(patientId) {
  return fetchJson(`${BASE_URL}/patients/${patientId}/changes`);
}
export async function getConflicts(patientId) {
  return fetchJson(`${BASE_URL}/patients/${patientId}/conflicts`);
}
export async function updateConflictStatus(patientId, conflictId, status, resolutionNotes = '') {
  return fetchJson(`${BASE_URL}/patients/${patientId}/conflicts/${conflictId}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status, resolution_notes: resolutionNotes }),
  });
}
export async function getGaps(patientId) {
  return fetchJson(`${BASE_URL}/patients/${patientId}/gaps`);
}
export async function getMilestones(patientId) {
  return fetchJson(`${BASE_URL}/patients/${patientId}/milestones`);
}
export async function getActionChains(patientId) {
  return fetchJson(`${BASE_URL}/patients/${patientId}/chains`);
}
export async function getJourneyGraph(patientId) {
  return fetchJson(`${BASE_URL}/patients/${patientId}/journey`);
}
export async function askQuestion(patientId, question) {
  return fetchJson(`${BASE_URL}/patients/${patientId}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
}

