from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ==================== PATIENT SCHEMAS ====================

class PatientBase(BaseModel):
    patient_reference: str = Field(..., description="Unique patient identifier e.g. PAT-2026-0814")
    name: str = Field(..., description="Patient full name")
    age: Optional[int] = None
    gender: Optional[str] = None


class PatientCreate(PatientBase):
    pass


class PatientOut(PatientBase):
    model_config = ConfigDict(from_attributes=True)

    patient_id: str
    created_at: datetime
    document_count: Optional[int] = 0
    event_count: Optional[int] = 0
    change_count: Optional[int] = 0
    conflict_count: Optional[int] = 0


# ==================== DOCUMENT SCHEMAS ====================

class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    patient_id: str
    filename: str
    original_filename: str
    document_type: str
    upload_date: datetime
    document_date: Optional[str] = None
    file_size: int
    page_count: int
    processing_status: str
    processing_stage: str
    error_message: Optional[str] = None
    created_at: datetime


class DocumentDetail(DocumentOut):
    extracted_text: Optional[str] = None


class DocumentProcessResponse(BaseModel):
    document_id: str
    processing_status: str
    processing_stage: str
    document_type: str
    document_date: Optional[str] = None
    events_extracted_count: int
    message: str


# ==================== AI EXTRACTION SCHEMA ====================

class ExtractedEntities(BaseModel):
    conditions: List[str] = Field(default_factory=list)
    symptoms: List[str] = Field(default_factory=list)
    tests: List[Dict[str, Any]] = Field(default_factory=list)
    medications: List[Dict[str, Any]] = Field(default_factory=list)
    procedures: List[str] = Field(default_factory=list)
    findings: List[str] = Field(default_factory=list)


class ExtractedEventItem(BaseModel):
    event_type: str = Field(..., description="condition | symptom | test | medication | procedure | clinical_finding | treatment | follow_up | discharge")
    event_date: Optional[str] = Field(None, description="Actual date event occurred (YYYY-MM-DD or standard display date). None if unknown.")
    event_date_type: str = Field("explicit", description="explicit | relative | approximate | unknown")
    description: str = Field(..., description="Human-readable event summary")
    entities: ExtractedEntities = Field(default_factory=ExtractedEntities)
    supporting_text: str = Field(..., description="Exact verbatim text snippet from document providing source evidence")
    source_page: Optional[int] = Field(1, description="Page number where evidence appears")
    confidence: float = Field(1.0, ge=0.0, le=1.0)


class DocumentExtractionResult(BaseModel):
    document_type: str = Field(..., description="lab_report | prescription | clinical_note | imaging_report | discharge_summary | other")
    document_date: Optional[str] = Field(None, description="When the document was authored/created")
    patient_reference: Optional[str] = None
    events: List[ExtractedEventItem] = Field(default_factory=list)


# ==================== TIMELINE & EVENT SCHEMAS ====================

class MedicalEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    patient_id: str
    source_document_id: str
    source_document_name: Optional[str] = None
    source_document_type: Optional[str] = None
    event_type: str
    event_date: Optional[str] = None
    event_date_type: str  # explicit | relative | approximate | unknown
    event_description: str
    structured_data: Optional[Dict[str, Any]] = None
    confidence: float
    source_page: Optional[int] = 1
    supporting_text: str
    created_at: datetime
    related_events: Optional[List[Dict[str, Any]]] = None

    # Phase 2: Priority Engine & Evidence Confidence Layer
    importance_priority: Optional[str] = "Moderate"
    importance_reason: Optional[str] = None
    evidence_level: Optional[str] = "Strong"
    evidence_rationale: Optional[str] = None


class EventRelationshipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    relationship_id: str
    patient_id: str
    source_event_id: str
    target_event_id: str
    source_event_desc: Optional[str] = None
    target_event_desc: Optional[str] = None
    relationship_type: str
    confidence: float
    explanation: Optional[str] = None
    created_at: datetime


class ChangeEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    change_id: str
    patient_id: str
    change_type: str  # medication_change | lab_trajectory | treatment_update | status_change
    item_name: str
    previous_value: Optional[str] = None
    new_value: str
    previous_event_id: Optional[str] = None
    new_event_id: Optional[str] = None
    explanation: str
    created_at: datetime

    # Phase 2: Change Significance Engine
    significance_category: Optional[str] = "routine_change"
    previous_date: Optional[str] = None
    new_date: Optional[str] = None
    source_evidence: Optional[str] = None


class ConflictOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    conflict_id: str
    patient_id: str
    event_type: str
    description: str
    related_event_ids: Optional[List[str]] = None
    source_a_doc_id: Optional[str] = None
    source_a_doc_name: Optional[str] = None
    source_a_text: Optional[str] = None
    source_b_doc_id: Optional[str] = None
    source_b_doc_name: Optional[str] = None
    source_b_text: Optional[str] = None
    status: str
    created_at: datetime

    # Phase 2: Clinical Conflict Resolution Workspace
    conflicting_item: Optional[str] = None
    source_a_date: Optional[str] = None
    source_b_date: Optional[str] = None
    source_a_page: Optional[int] = 1
    source_b_page: Optional[int] = 1
    review_reason: Optional[str] = None
    human_action_guidance: Optional[str] = None
    resolution_notes: Optional[str] = None


class ConflictStatusUpdate(BaseModel):
    status: str = Field(..., description="unresolved | under_review | resolved")
    resolution_notes: Optional[str] = None


class TimelineGapOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    gap_id: str
    patient_id: str
    from_event_id: Optional[str] = None
    from_event_desc: Optional[str] = None
    from_event_date: Optional[str] = None
    to_event_id: Optional[str] = None
    to_event_desc: Optional[str] = None
    to_event_date: Optional[str] = None
    days_gap: int
    gap_type: str
    description: str
    created_at: datetime

    # Phase 2: Timeline Gap Intelligence
    gap_start_date: Optional[str] = None
    gap_end_date: Optional[str] = None
    clinical_context: Optional[str] = None
    review_recommendation: Optional[str] = None


# Phase 2: Milestones & Decision Chains Schemas
class MilestoneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    milestone_id: str
    patient_id: str
    event_id: Optional[str] = None
    document_id: Optional[str] = None
    document_name: Optional[str] = None
    milestone_type: str
    title: str
    milestone_date: Optional[str] = None
    description: str
    supporting_text: Optional[str] = None
    source_page: Optional[int] = 1
    created_at: datetime


class ChainNode(BaseModel):
    event_id: str
    event_type: str
    event_date: Optional[str] = None
    description: str
    supporting_text: str
    source_document_name: Optional[str] = None
    relationship_to_next: Optional[str] = None  # resulted_in | followed_by | associated_with
    transition_explanation: Optional[str] = None


class ClinicalActionChain(BaseModel):
    chain_id: str
    chain_title: str
    domain: str  # e.g., Glycemic Management & Renal Transition, Hypertension
    summary: str
    nodes: List[ChainNode]


class PatientTimelineResponse(BaseModel):
    patient_id: str
    patient_name: str
    patient_reference: str
    total_events: int
    timeline_events: List[MedicalEventOut]
    date_range: Optional[Dict[str, Any]] = None



class PatientIntelligenceSummary(BaseModel):
    patient_id: str
    total_documents: int
    total_events: int
    changes_count: int
    conflicts_count: int
    gaps_count: int
    relationships_count: int
    milestones_count: Optional[int] = 0
    chains_count: Optional[int] = 0
    changes: List[ChangeEventOut]
    conflicts: List[ConflictOut]
    gaps: List[TimelineGapOut]
    relationships: List[EventRelationshipOut]
    milestones: Optional[List[MilestoneOut]] = Field(default_factory=list)
    chains: Optional[List[ClinicalActionChain]] = Field(default_factory=list)



# ==================== Q&A SCHEMAS ====================

class QASourceCitation(BaseModel):
    document_id: str
    document_name: str
    document_type: str
    event_id: Optional[str] = None
    page: Optional[int] = 1
    supporting_text: str
    event_date: Optional[str] = None


class QARequest(BaseModel):
    question: str


class QAResponse(BaseModel):
    question: str
    answer: str
    has_sufficient_evidence: bool
    citations: List[QASourceCitation]
