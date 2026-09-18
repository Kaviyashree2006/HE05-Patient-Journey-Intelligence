import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Index
)
from sqlalchemy.orm import relationship
from app.database.connection import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_reference = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String(16), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    documents = relationship("Document", back_populates="patient", cascade="all, delete-orphan")
    events = relationship("MedicalEvent", back_populates="patient", cascade="all, delete-orphan")
    relationships = relationship("EventRelationship", back_populates="patient", cascade="all, delete-orphan")
    changes = relationship("ChangeEvent", back_populates="patient", cascade="all, delete-orphan")
    conflicts = relationship("Conflict", back_populates="patient", cascade="all, delete-orphan")
    gaps = relationship("TimelineGap", back_populates="patient", cascade="all, delete-orphan")
    milestones = relationship("Milestone", back_populates="patient", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    document_id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    document_type = Column(String(64), default="unknown", index=True)  # lab_report, prescription, clinical_note, imaging_report, discharge_summary
    upload_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    document_date = Column(String(32), nullable=True)  # Date string when doc was created e.g. "2026-01-10"
    extracted_text = Column(Text, nullable=True)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, default=0)
    processing_status = Column(String(32), default="pending", index=True)  # pending, processing, completed, failed
    processing_stage = Column(String(64), default="uploaded")
    error_message = Column(Text, nullable=True)
    page_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    patient = relationship("Patient", back_populates="documents")
    events = relationship("MedicalEvent", back_populates="document", cascade="all, delete-orphan")


class MedicalEvent(Base):
    __tablename__ = "medical_events"

    event_id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False, index=True)
    source_document_id = Column(String(36), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False, index=True)

    event_type = Column(String(64), nullable=False, index=True)  # condition, symptom, test, medication, procedure, clinical_finding, treatment, follow_up, discharge
    event_date = Column(String(32), nullable=True, index=True)  # Normalized YYYY-MM-DD or standard display date
    event_date_type = Column(String(32), default="explicit", index=True)  # explicit, relative, approximate, unknown
    event_description = Column(Text, nullable=False)
    structured_data = Column(Text, nullable=True)  # JSON-encoded entities (tests, medications, doses, findings)
    confidence = Column(Float, default=1.0)
    source_page = Column(Integer, nullable=True, default=1)
    supporting_text = Column(Text, nullable=False)  # Verbatim quote from source document for evidence linkage

    # Phase 2: Priority & Evidence Confidence Layer
    importance_priority = Column(String(32), default="Moderate", index=True)  # Critical, High, Moderate, Informational
    importance_reason = Column(Text, nullable=True)
    evidence_level = Column(String(32), default="Strong", index=True)  # Strong, Moderate, Limited
    evidence_rationale = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    patient = relationship("Patient", back_populates="events")
    document = relationship("Document", back_populates="events")


class EventRelationship(Base):
    __tablename__ = "event_relationships"

    relationship_id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False, index=True)
    source_event_id = Column(String(36), ForeignKey("medical_events.event_id", ondelete="CASCADE"), nullable=False, index=True)
    target_event_id = Column(String(36), ForeignKey("medical_events.event_id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type = Column(String(64), nullable=False, index=True)  # resulted_in, followed_by, associated_with
    confidence = Column(Float, default=0.9)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    patient = relationship("Patient", back_populates="relationships")
    source_event = relationship("MedicalEvent", foreign_keys=[source_event_id])
    target_event = relationship("MedicalEvent", foreign_keys=[target_event_id])


class ChangeEvent(Base):
    __tablename__ = "change_events"

    change_id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False, index=True)
    change_type = Column(String(64), nullable=False, index=True)  # medication_change, lab_trajectory, treatment_update, status_change
    item_name = Column(String(128), nullable=False)  # e.g., "Metformin", "HbA1c", "eGFR"
    previous_value = Column(String(255), nullable=True)
    new_value = Column(String(255), nullable=False)
    previous_event_id = Column(String(36), ForeignKey("medical_events.event_id", ondelete="SET NULL"), nullable=True)
    new_event_id = Column(String(36), ForeignKey("medical_events.event_id", ondelete="SET NULL"), nullable=True)
    explanation = Column(Text, nullable=False)

    # Phase 2: Change Significance Engine
    significance_category = Column(String(64), default="routine_change", index=True)  # medication_started, medication_dose_increased, medication_held, lab_value_increased, lab_value_decreased, condition_status_changed, new_documented_finding
    previous_date = Column(String(32), nullable=True)
    new_date = Column(String(32), nullable=True)
    source_evidence = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    patient = relationship("Patient", back_populates="changes")
    previous_event = relationship("MedicalEvent", foreign_keys=[previous_event_id])
    new_event = relationship("MedicalEvent", foreign_keys=[new_event_id])


class Conflict(Base):
    __tablename__ = "conflicts"

    conflict_id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)  # allergy_discrepancy, medication_dose, clinical_status
    description = Column(Text, nullable=False)
    related_event_ids = Column(Text, nullable=True)  # JSON list of event UUIDs
    source_a_doc_id = Column(String(36), ForeignKey("documents.document_id", ondelete="SET NULL"), nullable=True)
    source_b_doc_id = Column(String(36), ForeignKey("documents.document_id", ondelete="SET NULL"), nullable=True)
    source_a_text = Column(Text, nullable=True)
    source_b_text = Column(Text, nullable=True)
    status = Column(String(32), default="unresolved")  # unresolved, under_review, resolved

    # Phase 2: Clinical Conflict Resolution Workspace
    conflicting_item = Column(String(128), nullable=True)  # e.g., "Penicillin Allergy"
    source_a_date = Column(String(32), nullable=True)
    source_b_date = Column(String(32), nullable=True)
    source_a_page = Column(Integer, nullable=True, default=1)
    source_b_page = Column(Integer, nullable=True, default=1)
    review_reason = Column(Text, nullable=True)
    human_action_guidance = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    patient = relationship("Patient", back_populates="conflicts")
    source_a_doc = relationship("Document", foreign_keys=[source_a_doc_id])
    source_b_doc = relationship("Document", foreign_keys=[source_b_doc_id])


class TimelineGap(Base):
    __tablename__ = "timeline_gaps"

    gap_id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False, index=True)
    from_event_id = Column(String(36), ForeignKey("medical_events.event_id", ondelete="SET NULL"), nullable=True)
    to_event_id = Column(String(36), ForeignKey("medical_events.event_id", ondelete="SET NULL"), nullable=True)
    days_gap = Column(Integer, nullable=False)
    gap_type = Column(String(64), default="unmonitored_interval")  # extended_interval_without_records
    description = Column(Text, nullable=False)

    # Phase 2: Timeline Gap Intelligence
    gap_start_date = Column(String(32), nullable=True)
    gap_end_date = Column(String(32), nullable=True)
    clinical_context = Column(Text, nullable=True)
    review_recommendation = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    patient = relationship("Patient", back_populates="gaps")
    from_event = relationship("MedicalEvent", foreign_keys=[from_event_id])
    to_event = relationship("MedicalEvent", foreign_keys=[to_event_id])


class Milestone(Base):
    __tablename__ = "milestones"

    milestone_id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(String(36), ForeignKey("medical_events.event_id", ondelete="SET NULL"), nullable=True, index=True)
    document_id = Column(String(36), ForeignKey("documents.document_id", ondelete="SET NULL"), nullable=True, index=True)
    milestone_type = Column(String(64), nullable=False, index=True)  # initial_presentation, diagnostic_investigation, clinical_consultation, treatment_initiation, therapy_adjustment, imaging_investigation, hospitalization, discharge
    title = Column(String(255), nullable=False)
    milestone_date = Column(String(32), nullable=True, index=True)
    description = Column(Text, nullable=False)
    supporting_text = Column(Text, nullable=True)
    source_page = Column(Integer, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    patient = relationship("Patient", back_populates="milestones")
    event = relationship("MedicalEvent")
    document = relationship("Document")

