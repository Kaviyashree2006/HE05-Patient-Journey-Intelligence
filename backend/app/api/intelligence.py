import json
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database import models
from app.schemas.models import (
    EventRelationshipOut,
    ChangeEventOut,
    ConflictOut,
    ConflictStatusUpdate,
    TimelineGapOut,
    MilestoneOut,
    ClinicalActionChain,
    PatientIntelligenceSummary
)
from app.services.milestone_engine import MilestoneEngine
from app.services.decision_chain_engine import DecisionChainEngine

router = APIRouter(prefix="/patients/{patient_id}", tags=["Intelligence & Relationships"])


def safe_parse_json_list(raw_val: Any) -> List[str]:
    if not raw_val:
        return []
    if isinstance(raw_val, list):
        return [str(x) for x in raw_val]
    try:
        val = json.loads(raw_val)
        return val if isinstance(val, list) else []
    except Exception:
        import ast
        try:
            val = ast.literal_eval(raw_val)
            return [str(x) for x in val] if isinstance(val, list) else []
        except Exception:
            return []



@router.get("/summary", response_model=PatientIntelligenceSummary)
def get_patient_summary(patient_id: str, db: Session = Depends(get_db)):
    p = db.query(models.Patient).filter(models.Patient.patient_id == patient_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found.")

    doc_count = db.query(models.Document).filter(models.Document.patient_id == patient_id).count()
    ev_count = db.query(models.MedicalEvent).filter(models.MedicalEvent.patient_id == patient_id).count()

    changes = get_patient_changes(patient_id, db)
    conflicts = get_patient_conflicts(patient_id, db)
    gaps = get_patient_gaps(patient_id, db)
    relationships = get_patient_relationships(patient_id, db)
    milestones = get_patient_milestones(patient_id, db)
    chains = get_patient_action_chains(patient_id, db)

    return PatientIntelligenceSummary(
        patient_id=patient_id,
        total_documents=doc_count,
        total_events=ev_count,
        changes_count=len(changes),
        conflicts_count=len(conflicts),
        gaps_count=len(gaps),
        relationships_count=len(relationships),
        milestones_count=len(milestones),
        chains_count=len(chains),
        changes=changes,
        conflicts=conflicts,
        gaps=gaps,
        relationships=relationships,
        milestones=milestones,
        chains=chains
    )


@router.get("/milestones", response_model=List[MilestoneOut])
def get_patient_milestones(patient_id: str, db: Session = Depends(get_db)):
    # Check if milestones exist in db
    db_milestones = db.query(models.Milestone).filter(models.Milestone.patient_id == patient_id).order_by(models.Milestone.milestone_date.asc()).all()
    if db_milestones:
        docs = {d.document_id: d.original_filename for d in db.query(models.Document).filter(models.Document.patient_id == patient_id).all()}
        return [
            MilestoneOut(
                milestone_id=m.milestone_id,
                patient_id=m.patient_id,
                event_id=m.event_id,
                document_id=m.document_id,
                document_name=docs.get(m.document_id, "Medical Document"),
                milestone_type=m.milestone_type,
                title=m.title,
                milestone_date=m.milestone_date,
                description=m.description,
                supporting_text=m.supporting_text,
                source_page=m.source_page or 1,
                created_at=m.created_at
            )
            for m in db_milestones
        ]

    # Synthesize dynamically if not seeded in db table
    events = db.query(models.MedicalEvent).filter(models.MedicalEvent.patient_id == patient_id).all()
    docs = db.query(models.Document).filter(models.Document.patient_id == patient_id).all()

    ev_dicts = [{
        "event_id": e.event_id,
        "source_document_id": e.source_document_id,
        "event_type": e.event_type,
        "event_date": e.event_date,
        "event_description": e.event_description,
        "supporting_text": e.supporting_text,
        "source_page": e.source_page
    } for e in events]

    doc_dicts = [{
        "document_id": d.document_id,
        "filename": d.filename,
        "original_filename": d.original_filename
    } for d in docs]

    extracted = MilestoneEngine.extract_milestones(ev_dicts, doc_dicts)
    import uuid
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    return [
        MilestoneOut(
            milestone_id=str(uuid.uuid4()),
            patient_id=patient_id,
            event_id=m.get("event_id"),
            document_id=m.get("document_id"),
            document_name=m.get("document_name"),
            milestone_type=m.get("milestone_type"),
            title=m.get("title"),
            milestone_date=m.get("milestone_date"),
            description=m.get("description"),
            supporting_text=m.get("supporting_text"),
            source_page=m.get("source_page") or 1,
            created_at=now
        )
        for m in extracted
    ]


@router.get("/chains", response_model=List[ClinicalActionChain])
def get_patient_action_chains(patient_id: str, db: Session = Depends(get_db)):
    events = db.query(models.MedicalEvent).filter(models.MedicalEvent.patient_id == patient_id).all()
    docs = db.query(models.Document).filter(models.Document.patient_id == patient_id).all()
    rels = db.query(models.EventRelationship).filter(models.EventRelationship.patient_id == patient_id).all()

    ev_dicts = [{
        "event_id": e.event_id,
        "source_document_id": e.source_document_id,
        "event_type": e.event_type,
        "event_date": e.event_date,
        "event_description": e.event_description,
        "supporting_text": e.supporting_text
    } for e in events]

    doc_dicts = [{
        "document_id": d.document_id,
        "filename": d.filename,
        "original_filename": d.original_filename
    } for d in docs]

    rel_dicts = [{
        "source_event_id": r.source_event_id,
        "target_event_id": r.target_event_id,
        "relationship_type": r.relationship_type,
        "explanation": r.explanation
    } for r in rels]

    return DecisionChainEngine.construct_chains(ev_dicts, rel_dicts, doc_dicts)


@router.patch("/conflicts/{conflict_id}/status", response_model=ConflictOut)
def update_conflict_status(
    patient_id: str,
    conflict_id: str,
    payload: ConflictStatusUpdate,
    db: Session = Depends(get_db)
):
    patient = db.query(models.Patient).filter(
        (models.Patient.patient_id == patient_id) | (models.Patient.patient_reference == patient_id)
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")

    conflict = db.query(models.Conflict).filter(
        models.Conflict.patient_id == patient.patient_id,
        models.Conflict.conflict_id == conflict_id
    ).first()
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found.")

    valid_statuses = {"unresolved", "under_review", "resolved"}
    if payload.status.lower() not in valid_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid conflict status '{payload.status}'. Allowed values are: unresolved, under_review, resolved."
        )

    conflict.status = payload.status.lower()
    if payload.resolution_notes is not None:
        conflict.resolution_notes = payload.resolution_notes
    db.commit()
    db.refresh(conflict)

    doc_a = db.query(models.Document).filter(models.Document.document_id == conflict.source_a_doc_id).first() if conflict.source_a_doc_id else None
    doc_b = db.query(models.Document).filter(models.Document.document_id == conflict.source_b_doc_id).first() if conflict.source_b_doc_id else None

    return ConflictOut(
        conflict_id=conflict.conflict_id,
        patient_id=conflict.patient_id,
        event_type=conflict.event_type,
        conflicting_item=conflict.conflicting_item,
        description=conflict.description,
        related_event_ids=safe_parse_json_list(conflict.related_event_ids),
        source_a_doc_id=conflict.source_a_doc_id,
        source_a_doc_name=doc_a.original_filename if doc_a else "Source Record A",
        source_a_date=conflict.source_a_date,
        source_a_page=conflict.source_a_page or 1,
        source_a_text=conflict.source_a_text,
        source_b_doc_id=conflict.source_b_doc_id,
        source_b_doc_name=doc_b.original_filename if doc_b else "Source Record B",
        source_b_date=conflict.source_b_date,
        source_b_page=conflict.source_b_page or 1,
        source_b_text=conflict.source_b_text,
        status=conflict.status,
        review_reason=conflict.review_reason,
        human_action_guidance=conflict.human_action_guidance,
        resolution_notes=conflict.resolution_notes,
        created_at=conflict.created_at
    )


@router.get("/relationships", response_model=List[EventRelationshipOut])
def get_patient_relationships(patient_id: str, db: Session = Depends(get_db)):
    rels = db.query(models.EventRelationship).filter(models.EventRelationship.patient_id == patient_id).all()
    results = []
    for r in rels:
        src_ev = db.query(models.MedicalEvent).filter(models.MedicalEvent.event_id == r.source_event_id).first()
        tgt_ev = db.query(models.MedicalEvent).filter(models.MedicalEvent.event_id == r.target_event_id).first()
        results.append(EventRelationshipOut(
            relationship_id=r.relationship_id,
            patient_id=r.patient_id,
            source_event_id=r.source_event_id,
            target_event_id=r.target_event_id,
            source_event_desc=src_ev.event_description if src_ev else "Source Event",
            target_event_desc=tgt_ev.event_description if tgt_ev else "Target Event",
            relationship_type=r.relationship_type,
            confidence=r.confidence,
            explanation=r.explanation,
            created_at=r.created_at
        ))
    return results


@router.get("/changes", response_model=List[ChangeEventOut])
def get_patient_changes(patient_id: str, db: Session = Depends(get_db)):
    db_changes = db.query(models.ChangeEvent).filter(models.ChangeEvent.patient_id == patient_id).order_by(models.ChangeEvent.created_at.desc()).all()
    results = []
    for c in db_changes:
        results.append(ChangeEventOut(
            change_id=c.change_id,
            patient_id=c.patient_id,
            change_type=c.change_type,
            significance_category=c.significance_category or "routine_change",
            item_name=c.item_name,
            previous_value=c.previous_value,
            new_value=c.new_value,
            previous_date=c.previous_date,
            new_date=c.new_date,
            previous_event_id=c.previous_event_id,
            new_event_id=c.new_event_id,
            source_evidence=c.source_evidence,
            explanation=c.explanation,
            created_at=c.created_at
        ))
    return results


@router.get("/conflicts", response_model=List[ConflictOut])
def get_patient_conflicts(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(
        (models.Patient.patient_id == patient_id) | (models.Patient.patient_reference == patient_id)
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    conflicts = db.query(models.Conflict).filter(models.Conflict.patient_id == patient.patient_id).all()
    results = []
    for c in conflicts:
        doc_a = db.query(models.Document).filter(models.Document.document_id == c.source_a_doc_id).first() if c.source_a_doc_id else None
        doc_b = db.query(models.Document).filter(models.Document.document_id == c.source_b_doc_id).first() if c.source_b_doc_id else None

        results.append(ConflictOut(
            conflict_id=c.conflict_id,
            patient_id=c.patient_id,
            event_type=c.event_type,
            conflicting_item=c.conflicting_item or "Clinical Discrepancy",
            description=c.description,
            related_event_ids=safe_parse_json_list(c.related_event_ids),
            source_a_doc_id=c.source_a_doc_id,
            source_a_doc_name=doc_a.original_filename if doc_a else "Source Record A",
            source_a_date=c.source_a_date,
            source_a_page=c.source_a_page or 1,
            source_a_text=c.source_a_text,
            source_b_doc_id=c.source_b_doc_id,
            source_b_doc_name=doc_b.original_filename if doc_b else "Source Record B",
            source_b_date=c.source_b_date,
            source_b_page=c.source_b_page or 1,
            source_b_text=c.source_b_text,
            status=c.status or "unresolved",
            review_reason=c.review_reason,
            human_action_guidance=c.human_action_guidance,
            resolution_notes=c.resolution_notes,
            created_at=c.created_at
        ))
    return results


@router.get("/gaps", response_model=List[TimelineGapOut])
def get_patient_gaps(patient_id: str, db: Session = Depends(get_db)):
    gaps = db.query(models.TimelineGap).filter(models.TimelineGap.patient_id == patient_id).all()
    results = []
    for g in gaps:
        ev_from = db.query(models.MedicalEvent).filter(models.MedicalEvent.event_id == g.from_event_id).first() if g.from_event_id else None
        ev_to = db.query(models.MedicalEvent).filter(models.MedicalEvent.event_id == g.to_event_id).first() if g.to_event_id else None

        results.append(TimelineGapOut(
            gap_id=g.gap_id,
            patient_id=g.patient_id,
            from_event_id=g.from_event_id,
            from_event_desc=ev_from.event_description if ev_from else "Prior Event",
            from_event_date=ev_from.event_date if ev_from else None,
            to_event_id=g.to_event_id,
            to_event_desc=ev_to.event_description if ev_to else "Subsequent Event",
            to_event_date=ev_to.event_date if ev_to else None,
            days_gap=g.days_gap,
            gap_start_date=g.gap_start_date or (ev_from.event_date if ev_from else None),
            gap_end_date=g.gap_end_date or (ev_to.event_date if ev_to else None),
            gap_type=g.gap_type,
            description=g.description,
            clinical_context=g.clinical_context,
            review_recommendation=g.review_recommendation,
            created_at=g.created_at
        ))
    return results



@router.get("/journey")
def get_patient_journey_graph(patient_id: str, db: Session = Depends(get_db)):
    """Returns nodes and edges structure for graph visualization of patient journey."""
    events = db.query(models.MedicalEvent).filter(models.MedicalEvent.patient_id == patient_id).all()
    rels = db.query(models.EventRelationship).filter(models.EventRelationship.patient_id == patient_id).all()
    docs = db.query(models.Document).filter(models.Document.patient_id == patient_id).all()
    doc_map = {d.document_id: d.original_filename for d in docs}

    nodes = []
    for ev in events:
        nodes.append({
            "id": ev.event_id,
            "label": ev.event_description[:45] + ("..." if len(ev.event_description) > 45 else ""),
            "full_label": ev.event_description,
            "event_type": ev.event_type,
            "event_date": ev.event_date or "Unknown Date",
            "date_type": ev.event_date_type,
            "document_name": doc_map.get(ev.source_document_id, "Document"),
            "supporting_text": ev.supporting_text
        })

    edges = []
    for r in rels:
        edges.append({
            "id": r.relationship_id,
            "source": r.source_event_id,
            "target": r.target_event_id,
            "label": r.relationship_type.replace("_", " "),
            "type": r.relationship_type,
            "explanation": r.explanation
        })

    return {
        "patient_id": patient_id,
        "nodes": nodes,
        "edges": edges
    }
