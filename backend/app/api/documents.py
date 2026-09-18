import os
import json
import shutil
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database import models
from app.schemas.models import DocumentOut, DocumentDetail, DocumentProcessResponse
from app.document_processing.extractor import DocumentExtractor, DocumentExtractionError
from app.document_processing.classifier import DocumentClassifier
from app.ai.hybrid_pipeline import HybridExtractionPipeline
from app.services.relationship_engine import RelationshipEngine
from app.services.change_detector import ChangeDetector
from app.services.conflict_detector import ConflictDetector
from app.services.gap_detector import GapDetector
from app.services.priority_engine import PriorityEngine
from app.services.evidence_confidence_engine import EvidenceConfidenceEngine
from app.services.milestone_engine import MilestoneEngine

router = APIRouter(tags=["Documents"])
UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)
pipeline = HybridExtractionPipeline()


async def process_document_internal(doc_record: models.Document, db: Session) -> DocumentProcessResponse:
    """Runs extraction, event generation, and patient-level intelligence update."""
    doc_record.processing_status = "processing"
    doc_record.processing_stage = "text_extraction"
    db.commit()

    try:
        # 1. Text Extraction
        extracted = DocumentExtractor.extract(doc_record.file_path)
        doc_record.extracted_text = extracted["full_text"]
        doc_record.page_count = extracted["page_count"]
        doc_record.processing_stage = "ai_understanding"
        db.commit()

        # 2. Document Classification
        pred_type, _ = DocumentClassifier.classify(extracted["full_text"], doc_record.original_filename)
        doc_record.document_type = pred_type
        db.commit()

        # 3. AI / Structured Event Extraction
        doc_record.processing_stage = "event_extraction"
        db.commit()

        ai_res = await pipeline.extract_document(
            text=extracted["full_text"],
            filename=doc_record.original_filename,
            predicted_type=pred_type,
            pages=extracted["pages"]
        )

        doc_record.document_type = ai_res.document_type
        doc_record.document_date = ai_res.document_date

        # Clear existing events for this document to avoid duplicates on re-process
        db.query(models.MedicalEvent).filter(models.MedicalEvent.source_document_id == doc_record.document_id).delete()
        db.commit()

        # Save Medical Events with Priority & Evidence Confidence
        events_created = 0
        for ev in ai_res.events:
            structured_str = ev.entities.model_dump_json() if hasattr(ev.entities, "model_dump_json") else "{}"
            
            p_level, p_reason = PriorityEngine.evaluate_priority({
                "event_description": ev.description,
                "supporting_text": ev.supporting_text,
                "event_type": ev.event_type
            })
            e_level, e_reason = EvidenceConfidenceEngine.evaluate_confidence({
                "event_description": ev.description,
                "supporting_text": ev.supporting_text,
                "event_type": ev.event_type,
                "event_date_type": ev.event_date_type
            })

            me = models.MedicalEvent(
                patient_id=doc_record.patient_id,
                source_document_id=doc_record.document_id,
                event_type=ev.event_type,
                event_date=ev.event_date,
                event_date_type=ev.event_date_type,
                event_description=ev.description,
                structured_data=structured_str,
                confidence=ev.confidence,
                source_page=ev.source_page or 1,
                supporting_text=ev.supporting_text,
                importance_priority=p_level,
                importance_reason=p_reason,
                evidence_level=e_level,
                evidence_rationale=e_reason
            )
            db.add(me)
            events_created += 1

        doc_record.processing_stage = "relationship_processing"
        db.commit()

        # 4. Refresh patient-level intelligence (relationships, changes, conflicts, gaps, milestones)
        refresh_patient_intelligence(doc_record.patient_id, db)

        doc_record.processing_status = "completed"
        doc_record.processing_stage = "completed"
        doc_record.error_message = None
        db.commit()

        return DocumentProcessResponse(
            document_id=doc_record.document_id,
            processing_status="completed",
            processing_stage="completed",
            document_type=doc_record.document_type,
            document_date=doc_record.document_date,
            events_extracted_count=events_created,
            message="Document successfully processed and timeline generated."
        )

    except Exception as e:
        doc_record.processing_status = "failed"
        doc_record.error_message = str(e)
        db.commit()
        return DocumentProcessResponse(
            document_id=doc_record.document_id,
            processing_status="failed",
            processing_stage="failed",
            document_type=doc_record.document_type,
            document_date=doc_record.document_date,
            events_extracted_count=0,
            message=f"Processing failed: {str(e)}"
        )


def refresh_patient_intelligence(patient_id: str, db: Session):
    """Recomputes relationships, changes, conflicts, gaps, and milestones across all patient events."""
    all_events = db.query(models.MedicalEvent).filter(models.MedicalEvent.patient_id == patient_id).all()
    all_docs = db.query(models.Document).filter(models.Document.patient_id == patient_id).all()

    event_dicts = [{
        "event_id": e.event_id,
        "patient_id": e.patient_id,
        "source_document_id": e.source_document_id,
        "event_type": e.event_type,
        "event_date": e.event_date,
        "event_date_type": e.event_date_type,
        "event_description": e.event_description,
        "supporting_text": e.supporting_text,
        "source_page": e.source_page,
        "confidence": e.confidence
    } for e in all_events]

    doc_dicts = [{
        "document_id": d.document_id,
        "filename": d.filename,
        "original_filename": d.original_filename,
        "document_type": d.document_type,
        "document_date": d.document_date
    } for d in all_docs]

    # Clear previous derived intelligence
    db.query(models.EventRelationship).filter(models.EventRelationship.patient_id == patient_id).delete()
    db.query(models.ChangeEvent).filter(models.ChangeEvent.patient_id == patient_id).delete()
    db.query(models.Conflict).filter(models.Conflict.patient_id == patient_id).delete()
    db.query(models.TimelineGap).filter(models.TimelineGap.patient_id == patient_id).delete()
    db.query(models.Milestone).filter(models.Milestone.patient_id == patient_id).delete()
    db.commit()

    # Discover and store relationships
    rels = RelationshipEngine.discover_relationships(event_dicts)
    for r in rels:
        db.add(models.EventRelationship(
            patient_id=patient_id,
            source_event_id=r["source_event_id"],
            target_event_id=r["target_event_id"],
            relationship_type=r["relationship_type"],
            confidence=r["confidence"],
            explanation=r["explanation"]
        ))

    # Detect and store changes
    changes = ChangeDetector.detect_changes(event_dicts)
    for c in changes:
        db.add(models.ChangeEvent(
            patient_id=patient_id,
            change_type=c["change_type"],
            significance_category=c.get("significance_category", "routine_change"),
            item_name=c["item_name"],
            previous_value=c["previous_value"],
            new_value=c["new_value"],
            previous_date=c.get("previous_date"),
            new_date=c.get("new_date"),
            previous_event_id=c.get("previous_event_id"),
            new_event_id=c.get("new_event_id"),
            source_evidence=c.get("source_evidence"),
            explanation=c["explanation"]
        ))

    # Detect and store conflicts
    conflicts = ConflictDetector.detect_conflicts(event_dicts, doc_dicts)
    for conf in conflicts:
        db.add(models.Conflict(
            patient_id=patient_id,
            event_type=conf["event_type"],
            conflicting_item=conf.get("conflicting_item"),
            description=conf["description"],
            related_event_ids=json.dumps(conf.get("related_event_ids", [])),
            source_a_doc_id=conf.get("source_a_doc_id"),
            source_b_doc_id=conf.get("source_b_doc_id"),
            source_a_date=conf.get("source_a_date"),
            source_b_date=conf.get("source_b_date"),
            source_a_page=conf.get("source_a_page", 1),
            source_b_page=conf.get("source_b_page", 1),
            source_a_text=conf.get("source_a_text"),
            source_b_text=conf.get("source_b_text"),
            status=conf.get("status", "unresolved"),
            review_reason=conf.get("review_reason"),
            human_action_guidance=conf.get("human_action_guidance")
        ))

    # Detect and store gaps
    gaps = GapDetector.detect_gaps(event_dicts)
    for g in gaps:
        db.add(models.TimelineGap(
            patient_id=patient_id,
            from_event_id=g.get("from_event_id"),
            to_event_id=g.get("to_event_id"),
            days_gap=g["days_gap"],
            gap_start_date=g.get("gap_start_date"),
            gap_end_date=g.get("gap_end_date"),
            gap_type=g["gap_type"],
            description=g["description"],
            clinical_context=g.get("clinical_context"),
            review_recommendation=g.get("review_recommendation")
        ))

    # Extract and store milestones
    milestones = MilestoneEngine.extract_milestones(event_dicts, doc_dicts)
    for m in milestones:
        db.add(models.Milestone(
            patient_id=patient_id,
            event_id=m.get("event_id"),
            document_id=m.get("document_id"),
            milestone_type=m.get("milestone_type"),
            title=m.get("title"),
            milestone_date=m.get("milestone_date"),
            description=m.get("description"),
            supporting_text=m.get("supporting_text"),
            source_page=m.get("source_page") or 1
        ))

    db.commit()



@router.post("/patients/{patient_id}/documents", response_model=List[DocumentOut])
async def upload_documents(
    patient_id: str,
    files: List[UploadFile] = File(...),
    auto_process: bool = True,
    db: Session = Depends(get_db)
):
    patient = db.query(models.Patient).filter(models.Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")

    saved_docs = []
    for upload in files:
        # Validate extension
        ext = os.path.splitext(upload.filename)[1].lower()
        if ext not in [".pdf", ".txt", ".png", ".jpg", ".jpeg"]:
            continue

        safe_filename = f"{patient.patient_reference}_{upload.filename}"
        target_path = os.path.join(UPLOAD_DIR, safe_filename)

        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)

        file_size = os.path.getsize(target_path)

        doc_record = models.Document(
            patient_id=patient.patient_id,
            filename=safe_filename,
            original_filename=upload.filename,
            file_path=target_path,
            file_size=file_size,
            processing_status="pending",
            processing_stage="uploaded"
        )
        db.add(doc_record)
        db.commit()
        db.refresh(doc_record)

        if auto_process:
            await process_document_internal(doc_record, db)

        saved_docs.append(doc_record)

    return saved_docs


@router.get("/patients/{patient_id}/documents", response_model=List[DocumentOut])
def list_patient_documents(patient_id: str, db: Session = Depends(get_db)):
    return db.query(models.Document).filter(models.Document.patient_id == patient_id).order_by(models.Document.upload_date.desc()).all()


@router.get("/documents/{document_id}", response_model=DocumentDetail)
def get_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(models.Document).filter(models.Document.document_id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc


def resolve_document_file_path(doc: models.Document) -> str:
    """Robustly locates the physical document file on disk across potential runtime directories."""
    candidate_paths = []
    
    # 1. Path stored in database record
    if doc.file_path:
        candidate_paths.append(doc.file_path)
        if not os.path.isabs(doc.file_path):
            candidate_paths.append(os.path.abspath(doc.file_path))
            candidate_paths.append(os.path.join(os.getcwd(), doc.file_path))

    # 2. Uploads folder
    if doc.filename:
        candidate_paths.append(os.path.join(UPLOAD_DIR, doc.filename))
    if doc.original_filename:
        candidate_paths.append(os.path.join(UPLOAD_DIR, doc.original_filename))

    # 3. Sample documents folder (for seeded synthetic corpus)
    sample_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "demo_data", "sample_documents"))
    if doc.filename:
        candidate_paths.append(os.path.join(sample_dir, doc.filename))
    if doc.original_filename:
        candidate_paths.append(os.path.join(sample_dir, doc.original_filename))

    for p in candidate_paths:
        if p and os.path.exists(p) and os.path.isfile(p):
            return os.path.abspath(p)

    raise HTTPException(
        status_code=404,
        detail=f"Physical file for document '{doc.original_filename or doc.document_id}' not found on server."
    )


@router.get("/documents/{document_id}/view")
def view_document_pdf(document_id: str, db: Session = Depends(get_db)):
    """Serves the document inline for browser and embedded PDF viewing."""
    doc = db.query(models.Document).filter(models.Document.document_id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    file_path = resolve_document_file_path(doc)
    media_type = "application/pdf" if file_path.lower().endswith(".pdf") else "text/plain"

    return FileResponse(
        file_path,
        media_type=media_type,
        content_disposition_type="inline",
        filename=doc.original_filename
    )


@router.get("/documents/{document_id}/download")
def download_document_file(document_id: str, db: Session = Depends(get_db)):
    """Serves the document as an attachment download with original filename."""
    doc = db.query(models.Document).filter(models.Document.document_id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    file_path = resolve_document_file_path(doc)
    media_type = "application/pdf" if file_path.lower().endswith(".pdf") else "application/octet-stream"

    return FileResponse(
        file_path,
        media_type=media_type,
        content_disposition_type="attachment",
        filename=doc.original_filename
    )


@router.get("/documents/{document_id}/file")
def get_document_file(document_id: str, disposition: str = "attachment", db: Session = Depends(get_db)):
    """Backward-compatible file endpoint supporting disposition query param ('attachment' or 'inline')."""
    doc = db.query(models.Document).filter(models.Document.document_id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    file_path = resolve_document_file_path(doc)
    media_type = "application/pdf" if file_path.lower().endswith(".pdf") else "text/plain"
    content_disposition = "inline" if disposition.lower() == "inline" else "attachment"

    return FileResponse(
        file_path,
        media_type=media_type,
        content_disposition_type=content_disposition,
        filename=doc.original_filename
    )


@router.post("/documents/{document_id}/process", response_model=DocumentProcessResponse)
async def trigger_document_process(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(models.Document).filter(models.Document.document_id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return await process_document_internal(doc, db)
