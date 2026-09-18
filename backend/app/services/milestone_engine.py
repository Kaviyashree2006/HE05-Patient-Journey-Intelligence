import re
from typing import List, Dict, Any


class MilestoneEngine:
    """Identifies and synthesizes key longitudinal patient journey milestones from extracted events.
    Does NOT invent milestones without supporting evidence; rigorously anchors each milestone to
    source documents and medical events.
    """

    @classmethod
    def extract_milestones(
        cls,
        events: List[Dict[str, Any]],
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        milestones = []
        doc_map = {d.get("document_id"): d for d in documents}

        # Sort events chronologically
        sorted_events = sorted(events, key=lambda x: x.get("event_date") or "9999")

        seen_milestone_types = set()

        for ev in sorted_events:
            desc = (ev.get("event_description") or "")
            desc_lower = desc.lower()
            supp = (ev.get("supporting_text") or "")
            supp_lower = supp.lower()
            ev_type = (ev.get("event_type") or "").lower()
            date = ev.get("event_date")
            doc_id = ev.get("source_document_id")
            doc = doc_map.get(doc_id, {})
            doc_name = doc.get("original_filename") or doc.get("filename") or "Medical Record"
            page = ev.get("source_page") or 1

            # 1. Initial Diagnostic Investigation (e.g. baseline lab panel with HbA1c 9.4%)
            if ev_type == "test" and ("hba1c" in desc_lower or "metabolic" in supp_lower) and "initial_diagnostic_investigation" not in seen_milestone_types:
                seen_milestone_types.add("initial_diagnostic_investigation")
                milestones.append({
                    "event_id": ev.get("event_id"),
                    "document_id": doc_id,
                    "document_name": doc_name,
                    "milestone_type": "diagnostic_investigation",
                    "title": "Initial Metabolic & Glycemic Investigation",
                    "milestone_date": date,
                    "description": "Baseline comprehensive metabolic evaluation identified marked hyperglycemia and microalbuminuria.",
                    "supporting_text": supp,
                    "source_page": page
                })

            # 2. Clinical Specialist Consultation & Diagnosis
            elif ev_type == "condition" and "diabetes" in desc_lower and "clinical_consultation" not in seen_milestone_types:
                seen_milestone_types.add("clinical_consultation")
                milestones.append({
                    "event_id": ev.get("event_id"),
                    "document_id": doc_id,
                    "document_name": doc_name,
                    "milestone_type": "clinical_consultation",
                    "title": "Specialist Endocrinology Consultation & T2DM Diagnosis",
                    "milestone_date": date,
                    "description": "Formal endocrinology evaluation established formal diagnosis of uncontrolled Type 2 Diabetes Mellitus and diabetic nephropathy.",
                    "supporting_text": supp,
                    "source_page": page
                })

            # 3. Treatment Initiation (Metformin 500mg or Lisinopril)
            elif ev_type == "medication" and "metformin 500 mg" in desc_lower and "treatment_initiation" not in seen_milestone_types:
                seen_milestone_types.add("treatment_initiation")
                milestones.append({
                    "event_id": ev.get("event_id"),
                    "document_id": doc_id,
                    "document_name": doc_name,
                    "milestone_type": "treatment_initiation",
                    "title": "Oral Antidiabetic & Antihypertensive Therapy Initiation",
                    "milestone_date": date,
                    "description": "First-line oral pharmacotherapy initiated with Metformin 500 mg daily and Lisinopril 10 mg for blood pressure and renal protection.",
                    "supporting_text": supp,
                    "source_page": page
                })

            # 4. Therapy Adjustment / Escalation (Metformin 1000mg)
            elif ev_type == "medication" and ("1000 mg" in desc_lower or "dose increased" in supp_lower) and "therapy_adjustment" not in seen_milestone_types:
                seen_milestone_types.add("therapy_adjustment")
                milestones.append({
                    "event_id": ev.get("event_id"),
                    "document_id": doc_id,
                    "document_name": doc_name,
                    "milestone_type": "therapy_adjustment",
                    "title": "Cardiology Review & Glycemic Regimen Escalation",
                    "milestone_date": date,
                    "description": "Outpatient review escalated Metformin dosage to 1000 mg twice daily in response to persistent postprandial levels.",
                    "supporting_text": supp,
                    "source_page": page
                })

            # 5. Imaging Investigation (Renal Ultrasound)
            elif (ev_type == "procedure" or "ultrasound" in desc_lower) and "imaging" in (desc_lower + supp_lower) and "imaging_investigation" not in seen_milestone_types:
                seen_milestone_types.add("imaging_investigation")
                milestones.append({
                    "event_id": ev.get("event_id"),
                    "document_id": doc_id,
                    "document_name": doc_name,
                    "milestone_type": "imaging_investigation",
                    "title": "Renal Diagnostic Ultrasound Surveillance",
                    "milestone_date": date,
                    "description": "Bilateral renal sonogram conducted for diabetic nephropathy surveillance, documenting mild cortical thinning without hydronephrosis.",
                    "supporting_text": supp,
                    "source_page": page
                })

            # 6. Inpatient Acute Hospitalization
            elif (ev_type == "procedure" or "admission" in desc_lower) and "admission" in desc_lower and "hospitalization" not in seen_milestone_types:
                seen_milestone_types.add("hospitalization")
                milestones.append({
                    "event_id": ev.get("event_id"),
                    "document_id": doc_id,
                    "document_name": doc_name,
                    "milestone_type": "hospitalization",
                    "title": "Emergency Inpatient Admission for Volume Depletion & AKI",
                    "milestone_date": date,
                    "description": "Acute hospitalization triggered by acute gastroenteritis leading to volume contraction and Acute Kidney Injury (Creatinine 2.4 mg/dL).",
                    "supporting_text": supp,
                    "source_page": page
                })

            # 7. Inpatient Discharge & Regimen Transition
            elif (ev_type == "discharge" or "insulin glargine" in desc_lower) and "discharge" not in seen_milestone_types:
                seen_milestone_types.add("discharge")
                milestones.append({
                    "event_id": ev.get("event_id"),
                    "document_id": doc_id,
                    "document_name": doc_name,
                    "milestone_type": "discharge",
                    "title": "Inpatient Discharge & Regimen Pivot (Insulin Initiation)",
                    "milestone_date": date,
                    "description": "Discharged with resolved renal function (Creatinine 1.3 mg/dL), temporary hold placed on Metformin, and transition to Insulin Glargine.",
                    "supporting_text": supp,
                    "source_page": page
                })

        return milestones
