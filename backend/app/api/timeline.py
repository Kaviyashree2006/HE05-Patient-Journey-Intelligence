import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database import models
from app.schemas.models import MedicalEventOut, PatientTimelineResponse
from app.services.temporal_engine import TemporalEngine

router = APIRouter(tags=["Timeline"])


@router.get("/patients/{patient_id}/timeline", response_model=PatientTimelineResponse)
def get_patient_timeline(
    patient_id: str,
    event_type: Optional[str] = Query(None, description="Filter by event_type: test, medication, condition, procedure, discharge, clinical_finding"),
    certainty: Optional[str] = Query(None, description="Filter by certainty: explicit, relative, approximate, unknown"),
    priority: Optional[str] = Query(None, description="Filter by priority: Critical, High, Moderate, Informational"),
    evidence_level: Optional[str] = Query(None, description="Filter by evidence_level: Strong, Moderate, Limited"),
    search: Optional[str] = Query(None, description="Text search across description and supporting text"),
    db: Session = Depends(get_db)
):
    patient = db.query(models.Patient).filter(
        (models.Patient.patient_id == patient_id) | (models.Patient.patient_reference == patient_id)
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    
    patient_id = patient.patient_id
    query = db.query(models.MedicalEvent).filter(models.MedicalEvent.patient_id == patient_id)

    if event_type:
        query = query.filter(models.MedicalEvent.event_type == event_type.lower())
    if certainty:
        query = query.filter(models.MedicalEvent.event_date_type == certainty.lower())
    if priority:
        query = query.filter(models.MedicalEvent.importance_priority == priority.capitalize())
    if evidence_level:
        query = query.filter(models.MedicalEvent.evidence_level == evidence_level.capitalize())
    if search:
        s = f"%{search}%"
        query = query.filter(
            (models.MedicalEvent.event_description.ilike(s)) |
            (models.MedicalEvent.supporting_text.ilike(s))
        )

    db_events = query.all()

    # Pre-fetch all documents for this patient for quick name lookup
    docs = db.query(models.Document).filter(models.Document.patient_id == patient_id).all()
    doc_map = {d.document_id: d for d in docs}

    event_dicts = []
    for ev in db_events:
        d = doc_map.get(ev.source_document_id)
        doc_name = d.original_filename if d else "Document"
        doc_type = d.document_type if d else "medical_record"

        structured_dict = None
        if ev.structured_data:
            try:
                structured_dict = json.loads(ev.structured_data)
            except Exception:
                structured_dict = {}

        event_dicts.append({
            "event_id": ev.event_id,
            "patient_id": ev.patient_id,
            "source_document_id": ev.source_document_id,
            "source_document_name": doc_name,
            "source_document_type": doc_type,
            "event_type": ev.event_type,
            "event_date": ev.event_date,
            "event_date_type": ev.event_date_type,
            "event_description": ev.event_description,
            "structured_data": structured_dict,
            "confidence": ev.confidence,
            "source_page": ev.source_page or 1,
            "supporting_text": ev.supporting_text,
            "importance_priority": ev.importance_priority or "Moderate",
            "importance_reason": ev.importance_reason,
            "evidence_level": ev.evidence_level or "Strong",
            "evidence_rationale": ev.evidence_rationale,
            "created_at": ev.created_at
        })

    # Sort events chronologically
    sorted_events = TemporalEngine.sort_events_chronologically(event_dicts)
    date_range = TemporalEngine.calculate_date_range(sorted_events)

    return PatientTimelineResponse(
        patient_id=patient.patient_id,
        patient_name=patient.name,
        patient_reference=patient.patient_reference,
        total_events=len(sorted_events),
        timeline_events=[MedicalEventOut(**e) for e in sorted_events],
        date_range=date_range
    )


@router.get("/events/{event_id}", response_model=MedicalEventOut)
def get_event_detail(event_id: str, db: Session = Depends(get_db)):
    ev = db.query(models.MedicalEvent).filter(models.MedicalEvent.event_id == event_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Medical event not found.")

    doc = db.query(models.Document).filter(models.Document.document_id == ev.source_document_id).first()
    doc_name = doc.original_filename if doc else "Document"
    doc_type = doc.document_type if doc else "medical_record"

    # Find connected relationships
    rels = db.query(models.EventRelationship).filter(
        (models.EventRelationship.source_event_id == event_id) |
        (models.EventRelationship.target_event_id == event_id)
    ).all()

    related_events = []
    for r in rels:
        is_source = (r.source_event_id == event_id)
        other_id = r.target_event_id if is_source else r.source_event_id
        other_ev = db.query(models.MedicalEvent).filter(models.MedicalEvent.event_id == other_id).first()
        if other_ev:
            related_events.append({
                "relationship_type": r.relationship_type,
                "direction": "targets" if is_source else "source_of",
                "related_event_id": other_id,
                "related_event_desc": other_ev.event_description,
                "related_event_date": other_ev.event_date,
                "explanation": r.explanation
            })

    structured_dict = None
    if ev.structured_data:
        try:
            structured_dict = json.loads(ev.structured_data)
        except Exception:
            structured_dict = {}

    return MedicalEventOut(
        event_id=ev.event_id,
        patient_id=ev.patient_id,
        source_document_id=ev.source_document_id,
        source_document_name=doc_name,
        source_document_type=doc_type,
        event_type=ev.event_type,
        event_date=ev.event_date,
        event_date_type=ev.event_date_type,
        event_description=ev.event_description,
        structured_data=structured_dict,
        confidence=ev.confidence,
        source_page=ev.source_page or 1,
        supporting_text=ev.supporting_text,
        importance_priority=ev.importance_priority or "Moderate",
        importance_reason=ev.importance_reason,
        evidence_level=ev.evidence_level or "Strong",
        evidence_rationale=ev.evidence_rationale,
        created_at=ev.created_at,
        related_events=related_events
    )

