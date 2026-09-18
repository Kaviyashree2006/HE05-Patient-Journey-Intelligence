from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database import models
from app.schemas.models import QARequest, QAResponse
from app.services.qa_engine import QAEngine

router = APIRouter(prefix="/patients/{patient_id}", tags=["Evidence Q&A"])


@router.post("/ask", response_model=QAResponse)
async def ask_patient_history(patient_id: str, payload: QARequest, db: Session = Depends(get_db)):
    if not payload.question or not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty or whitespace only.")

    patient = db.query(models.Patient).filter(
        (models.Patient.patient_id == patient_id) | (models.Patient.patient_reference == patient_id)
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    
    patient_id = patient.patient_id

    events = db.query(models.MedicalEvent).filter(models.MedicalEvent.patient_id == patient_id).all()
    docs = db.query(models.Document).filter(models.Document.patient_id == patient_id).all()
    db_changes = db.query(models.ChangeEvent).filter(models.ChangeEvent.patient_id == patient_id).all()
    db_conflicts = db.query(models.Conflict).filter(models.Conflict.patient_id == patient_id).all()
    db_gaps = db.query(models.TimelineGap).filter(models.TimelineGap.patient_id == patient_id).all()

    event_dicts = [{
        "event_id": e.event_id,
        "source_document_id": e.source_document_id,
        "event_type": e.event_type,
        "event_date": e.event_date,
        "event_date_type": e.event_date_type,
        "event_description": e.event_description,
        "supporting_text": e.supporting_text,
        "source_page": e.source_page
    } for e in events]

    doc_dicts = [{
        "document_id": d.document_id,
        "filename": d.filename,
        "original_filename": d.original_filename,
        "document_type": d.document_type
    } for d in docs]

    change_dicts = [{
        "item_name": c.item_name,
        "change_type": c.change_type,
        "significance_category": c.significance_category,
        "previous_value": c.previous_value,
        "new_value": c.new_value,
        "explanation": c.explanation,
        "previous_event_id": c.previous_event_id,
        "new_event_id": c.new_event_id
    } for c in db_changes]

    conflict_dicts = [{
        "conflicting_item": c.conflicting_item,
        "description": c.description,
        "source_a_text": c.source_a_text,
        "source_b_text": c.source_b_text,
        "status": c.status
    } for c in db_conflicts]

    gap_dicts = [{
        "days_gap": g.days_gap,
        "gap_start_date": g.gap_start_date,
        "gap_end_date": g.gap_end_date,
        "description": g.description,
        "from_event_id": g.from_event_id,
        "to_event_id": g.to_event_id
    } for g in db_gaps]

    return await QAEngine.answer_question(
        question=payload.question,
        events=event_dicts,
        documents=doc_dicts,
        changes=change_dicts,
        conflicts=conflict_dicts,
        gaps=gap_dicts
    )

