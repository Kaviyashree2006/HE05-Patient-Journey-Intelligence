import os
import json
import pymupdf as fitz
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.database import models
from app.document_processing.extractor import DocumentExtractor
from app.document_processing.classifier import DocumentClassifier
from app.ai.rule_extractor import ClinicalRuleExtractor
from app.services.relationship_engine import RelationshipEngine
from app.services.change_detector import ChangeDetector
from app.services.conflict_detector import ConflictDetector
from app.services.gap_detector import GapDetector
from app.services.priority_engine import PriorityEngine
from app.services.evidence_confidence_engine import EvidenceConfidenceEngine
from app.services.milestone_engine import MilestoneEngine

DEMO_DATA_DIR = os.path.join(os.path.dirname(__file__), "sample_documents")


def build_pdf_document(file_path: str, title: str, sections: List[Dict[str, str]]):
    """Creates a clean, realistic formatted medical PDF document."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)  # Standard Letter size

    # Header banner
    rect = fitz.Rect(36, 36, 576, 756)
    
    y = 54
    # Title
    page.insert_text(fitz.Point(36, y), "ST. JUDE HEALTH SYSTEM & REGIONAL MEDICAL CENTER", fontsize=12, color=(0.1, 0.2, 0.4))
    y += 18
    page.insert_text(fitz.Point(36, y), title.upper(), fontsize=15, color=(0.0, 0.1, 0.3))
    y += 14
    page.draw_line(fitz.Point(36, y), fitz.Point(576, y), color=(0.2, 0.4, 0.6), width=1.5)
    y += 24

    for sec in sections:
        header = sec.get("header", "")
        content = sec.get("content", "")

        if header:
            page.insert_text(fitz.Point(36, y), header, fontsize=11, color=(0.15, 0.25, 0.45))
            y += 16

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                y += 6
                continue
            if y > 730:
                page = doc.new_page(width=612, height=792)
                y = 54
            page.insert_text(fitz.Point(42, y), line, fontsize=9.5, color=(0.1, 0.1, 0.15))
            y += 14

        y += 10

    # Footer note
    page.draw_line(fitz.Point(36, 750), fitz.Point(576, 750), color=(0.7, 0.7, 0.7), width=0.5)
    page.insert_text(fitz.Point(36, 762), "SYNTHETIC DEMO DATA — HE-05 Medical Document Intelligence — Not for Clinical Use", fontsize=8, color=(0.5, 0.5, 0.5))

    doc.save(file_path)
    doc.close()


def generate_synthetic_documents() -> List[str]:
    """Generates 5 realistic PDF medical documents for synthetic patient Sarah Jenkins."""
    os.makedirs(DEMO_DATA_DIR, exist_ok=True)
    generated_files = []

    # 1. Initial Lab Report (10 Jan 2026)
    doc1_path = os.path.join(DEMO_DATA_DIR, "01_Initial_Lab_Report_Jan2026.pdf")
    doc1_sections = [
        {"header": "PATIENT DEMOGRAPHICS", "content": "Patient Name: Sarah Jenkins\nPatient ID: PAT-2026-0814\nDOB: 1972-04-12 | Age: 54 | Gender: Female\nCollection Date: 2026-01-10\nReport Date: 2026-01-10\nOrdering Physician: Dr. Michael Stone, MD"},
        {"header": "COMPREHENSIVE METABOLIC & GLYCEMIC PANEL", "content": "Test Name                     Result      Flag    Reference Interval   Units\n"
                                                                         "Hemoglobin A1c                9.4         HIGH    4.0 - 5.6            %\n"
                                                                         "Fasting Blood Glucose         210         HIGH    70 - 99              mg/dL\n"
                                                                         "Serum Creatinine              1.1         NORMAL  0.5 - 1.2            mg/dL\n"
                                                                         "eGFR                          72          NORMAL  > 60                 mL/min\n"
                                                                         "Total Cholesterol             228         HIGH    < 200                mg/dL\n"
                                                                         "Blood Pressure                142/88      HIGH    < 120/80             mmHg\n"
                                                                         "Urine Albumin/Creatinine      65          HIGH    < 30                 mg/g"},
        {"header": "LABORATORY INTERPRETATION", "content": "Significant marked hyperglycemia with elevated Hemoglobin A1c (9.4%) and microalbuminuria.\nRecommend clinical consultation and glycemic initiation."}
    ]
    build_pdf_document(doc1_path, "Diagnostic Laboratory Report", doc1_sections)
    generated_files.append(doc1_path)

    # 2. Endocrinology Clinical Consult (15 Jan 2026)
    doc2_path = os.path.join(DEMO_DATA_DIR, "02_Endocrinology_Clinical_Consult_Jan2026.pdf")
    doc2_sections = [
        {"header": "ENCOUNTER INFORMATION", "content": "Patient Name: Sarah Jenkins\nPatient ID: PAT-2026-0814\nEncounter Date: 2026-01-15\nConsulting Specialist: Dr. Robert Vance, MD (Endocrinology)\nClinic: Metro Center for Diabetes & Endocrinology"},
        {"header": "HISTORY OF PRESENT ILLNESS & ALLERGIES", "content": "Patient is a 54-year-old female referred for evaluation of newly identified marked hyperglycemia.\nPatient reports polyuria, polydipsia, and fatigue over past 4 weeks.\n\nAllergies: Penicillin (severe urticaria and facial angioedema)."},
        {"header": "CLINICAL ASSESSMENT", "content": "1. Type 2 Diabetes Mellitus - newly diagnosed, uncontrolled (HbA1c 9.4% on 2026-01-10).\n2. Essential Hypertension - suboptimally controlled.\n3. Early Diabetic Nephropathy with microalbuminuria."},
        {"header": "PLAN & TREATMENT", "content": "1. Prescribed Metformin 500 mg daily with dinner.\n2. Prescribed Lisinopril 10 mg daily for renal protection and blood pressure.\n3. Diabetes education referral and home blood glucose log.\n4. Repeat metabolic evaluation and follow-up in 4 weeks."}
    ]
    build_pdf_document(doc2_path, "Endocrinology Clinical Consultation Note", doc2_sections)
    generated_files.append(doc2_path)

    # 3. Cardiology Prescription Refill & Adjustment (18 Feb 2026)
    doc3_path = os.path.join(DEMO_DATA_DIR, "03_Cardiology_Prescription_Feb2026.pdf")
    doc3_sections = [
        {"header": "OUTPATIENT PRESCRIPTION ORDER", "content": "Patient Name: Sarah Jenkins\nPatient ID: PAT-2026-0814\nPrescription Date: 2026-02-18\nPrescriber: Dr. Elena Rostova, MD (Cardiovascular & Preventive Medicine)\nDEA: BR4829103 | NPI: 1892749102"},
        {"header": "MEDICATION ORDERS", "content": "Rx 1: Lisinopril 10 mg oral tablet\nSig: Take 1 tablet by mouth daily for Essential Hypertension.\nDispense: 90 tablets | Refills: 3\n\nRx 2: Metformin 1000 mg oral tablet\nSig: Take 1 tablet by mouth twice daily (dose increased from 500mg daily due to postprandial glucose levels).\nDispense: 180 tablets | Refills: 3"},
        {"header": "SPECIAL INSTRUCTIONS", "content": "Monitor renal function and blood pressure regularly. Avoid dehydration."}
    ]
    build_pdf_document(doc3_path, "Cardiology Outpatient Prescription Order", doc3_sections)
    generated_files.append(doc3_path)

    # 4. Renal Ultrasound Imaging Report (12 May 2026)
    doc4_path = os.path.join(DEMO_DATA_DIR, "04_Renal_Ultrasound_Imaging_May2026.pdf")
    doc4_sections = [
        {"header": "RADIOLOGY & IMAGING REPORT", "content": "Patient Name: Sarah Jenkins\nPatient ID: PAT-2026-0814\nExam Date: 2026-05-12\nDocument Date: 2026-05-12\nRadiologist: Dr. Karen Wu, MD\nStudy: Bilateral Renal Ultrasound Examination"},
        {"header": "CLINICAL INDICATION", "content": "Diabetic nephropathy surveillance in patient with Type 2 Diabetes Mellitus and microalbuminuria."},
        {"header": "FINDINGS", "content": "Right Kidney: Measures 10.4 cm in length. Mild bilateral cortical thinning noted.\nLeft Kidney: Measures 10.6 cm in length. Normal echogenicity.\nNo evidence of hydronephrosis, calculus, or perinephric fluid collection.\nRenal Doppler demonstrates patent bilateral renal vasculature with normal waveforms."},
        {"header": "IMPRESSION", "content": "1. Mild bilateral cortical thinning compatible with medical renal disease in patient with diabetic nephropathy.\n2. No hydronephrosis or acute obstructive uropathy."}
    ]
    build_pdf_document(doc4_path, "Diagnostic Imaging Report — Renal Ultrasound", doc4_sections)
    generated_files.append(doc4_path)

    # 5. Hospital Inpatient Discharge Summary (19 Aug 2026)
    doc5_path = os.path.join(DEMO_DATA_DIR, "05_Hospital_Discharge_Summary_Aug2026.pdf")
    doc5_sections = [
        {"header": "INPATIENT DISCHARGE SUMMARY", "content": "Patient Name: Sarah Jenkins\nPatient ID: PAT-2026-0814\nAdmission Date: 2026-08-14\nDischarge Date: 2026-08-19\nAttending Physician: Dr. Marcus Vance, MD\nDepartment: General Internal Medicine & Nephrology Inpatient Service"},
        {"header": "HOSPITAL COURSE & ADMISSION DETAILS", "content": "The patient presented with acute viral gastroenteritis, persistent emesis, and volume depletion.\nSerum Creatinine on admission was 2.4 mg/dL (Acute Kidney Injury superimposed on baseline diabetic nephropathy).\nResponded favorably to intravenous isotonic saline rehydration with serum creatinine improving to 1.3 mg/dL upon discharge.\n\nAllergies: No Known Drug Allergies (NKDA) / None recorded during intake."},
        {"header": "DISCHARGE MEDICATIONS & CHANGES", "content": "1. Metformin held temporarily due to recent acute kidney injury; do not resume until renal recheck.\n2. Prescribed Insulin Glargine 18 units subcutaneous daily at bedtime for glycemic management.\n3. Lisinopril 10 mg oral tablet daily resumed upon discharge.\n4. Follow-up renal panel in 14 days."}
    ]
    build_pdf_document(doc5_path, "Hospital Inpatient Discharge Summary", doc5_sections)
    generated_files.append(doc5_path)

    return generated_files


def seed_demo_patient_in_db(db: Session) -> models.Patient:
    """Seeds or resets the synthetic demo patient and runs full document intelligence pipeline."""
    # Check if patient exists
    patient = db.query(models.Patient).filter(models.Patient.patient_reference == "PAT-2026-0814").first()
    if patient:
        # Clean existing records for fresh re-seed
        db.delete(patient)
        db.commit()

    # Create synthetic patient
    patient = models.Patient(
        patient_reference="PAT-2026-0814",
        name="Sarah Jenkins",
        age=54,
        gender="Female"
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    # Ensure PDFs exist
    pdf_paths = generate_synthetic_documents()

    all_event_dicts = []
    all_doc_dicts = []

    for file_path in pdf_paths:
        filename = os.path.basename(file_path)
        extracted = DocumentExtractor.extract(file_path)
        text = extracted["full_text"]
        pred_type, _ = DocumentClassifier.classify(text, filename)

        rule_res = ClinicalRuleExtractor.extract(text, filename, pred_type, extracted["pages"])

        # Create Document record
        doc_record = models.Document(
            patient_id=patient.patient_id,
            filename=filename,
            original_filename=filename,
            document_type=rule_res.document_type,
            document_date=rule_res.document_date,
            extracted_text=text,
            file_path=file_path,
            file_size=os.path.getsize(file_path),
            page_count=extracted["page_count"],
            processing_status="completed",
            processing_stage="completed"
        )
        db.add(doc_record)
        db.commit()
        db.refresh(doc_record)

        all_doc_dicts.append({
            "document_id": doc_record.document_id,
            "filename": doc_record.filename,
            "original_filename": doc_record.original_filename,
            "document_type": doc_record.document_type,
            "document_date": doc_record.document_date
        })

        # Create MedicalEvent records
        for ev in rule_res.events:
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
            event_record = models.MedicalEvent(
                patient_id=patient.patient_id,
                source_document_id=doc_record.document_id,
                event_type=ev.event_type,
                event_date=ev.event_date,
                event_date_type=ev.event_date_type,
                event_description=ev.description,
                structured_data=ev.entities.model_dump_json() if hasattr(ev.entities, "model_dump_json") else "{}",
                confidence=ev.confidence,
                source_page=ev.source_page or 1,
                supporting_text=ev.supporting_text,
                importance_priority=p_level,
                importance_reason=p_reason,
                evidence_level=e_level,
                evidence_rationale=e_reason
            )
            db.add(event_record)
            db.commit()
            db.refresh(event_record)

            all_event_dicts.append({
                "event_id": event_record.event_id,
                "source_document_id": doc_record.document_id,
                "event_type": event_record.event_type,
                "event_date": event_record.event_date,
                "event_date_type": event_record.event_date_type,
                "event_description": event_record.event_description,
                "supporting_text": event_record.supporting_text,
                "source_page": event_record.source_page,
                "confidence": event_record.confidence,
                "importance_priority": event_record.importance_priority,
                "importance_reason": event_record.importance_reason,
                "evidence_level": event_record.evidence_level,
                "evidence_rationale": event_record.evidence_rationale
            })

    # Run Intelligence Engines on extracted events
    # 1. Relationships
    relationships = RelationshipEngine.discover_relationships(all_event_dicts)
    for r in relationships:
        rel_rec = models.EventRelationship(
            patient_id=patient.patient_id,
            source_event_id=r["source_event_id"],
            target_event_id=r["target_event_id"],
            relationship_type=r["relationship_type"],
            confidence=r["confidence"],
            explanation=r["explanation"]
        )
        db.add(rel_rec)

    # 2. Changes
    changes = ChangeDetector.detect_changes(all_event_dicts)
    for c in changes:
        chg_rec = models.ChangeEvent(
            patient_id=patient.patient_id,
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
        )
        db.add(chg_rec)

    # 3. Conflicts
    conflicts = ConflictDetector.detect_conflicts(all_event_dicts, all_doc_dicts)
    for conf in conflicts:
        conf_rec = models.Conflict(
            patient_id=patient.patient_id,
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
        )
        db.add(conf_rec)

    # 4. Gaps
    gaps = GapDetector.detect_gaps(all_event_dicts)
    for g in gaps:
        gap_rec = models.TimelineGap(
            patient_id=patient.patient_id,
            from_event_id=g.get("from_event_id"),
            to_event_id=g.get("to_event_id"),
            days_gap=g["days_gap"],
            gap_start_date=g.get("gap_start_date"),
            gap_end_date=g.get("gap_end_date"),
            gap_type=g["gap_type"],
            description=g["description"],
            clinical_context=g.get("clinical_context"),
            review_recommendation=g.get("review_recommendation")
        )
        db.add(gap_rec)

    # 5. Milestones
    milestones = MilestoneEngine.extract_milestones(all_event_dicts, all_doc_dicts)
    for m in milestones:
        m_rec = models.Milestone(
            patient_id=patient.patient_id,
            event_id=m.get("event_id"),
            document_id=m.get("document_id"),
            milestone_type=m.get("milestone_type"),
            title=m.get("title"),
            milestone_date=m.get("milestone_date"),
            description=m.get("description"),
            supporting_text=m.get("supporting_text"),
            source_page=m.get("source_page") or 1
        )
        db.add(m_rec)

    db.commit()
    db.refresh(patient)
    return patient
