import json
from typing import List, Dict, Any


class ConflictDetector:
    """Detects potential clinical discrepancies across heterogeneous medical documents.
    STRICTLY AVOIDS arbitrating medical truth; flags discrepancies for clinical reviewer investigation
    within the Clinical Conflict Resolution Workspace.
    """

    @classmethod
    def detect_conflicts(cls, events: List[Dict[str, Any]], documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        conflicts = []
        doc_map = {d.get("document_id"): d for d in documents}

        # 1. Allergy Discrepancy Detection (e.g. Penicillin allergy vs NKDA)
        allergy_records = []
        for ev in events:
            desc = ev.get("event_description", "")
            supp = ev.get("supporting_text", "")
            combined = f"{desc} {supp}".lower()

            doc_id = ev.get("source_document_id")
            doc = doc_map.get(doc_id, {})
            doc_name = doc.get("original_filename") or doc.get("filename") or "Unknown Document"
            doc_date = doc.get("document_date") or ev.get("event_date") or "Unknown Date"
            page = ev.get("source_page") or 1

            if "penicillin" in combined and ("allerg" in combined or "rash" in combined or "urticaria" in combined or "reaction" in combined or "angioedema" in combined):
                allergy_records.append({
                    "type": "has_allergy",
                    "agent": "Penicillin Allergy",
                    "event_id": ev.get("event_id"),
                    "doc_id": doc_id,
                    "doc_name": doc_name,
                    "doc_date": doc_date,
                    "page": page,
                    "text": supp or desc
                })
            elif "nkda" in combined or "no known" in combined or "none recorded" in combined:
                allergy_records.append({
                    "type": "no_allergies",
                    "agent": "Penicillin Allergy",
                    "event_id": ev.get("event_id"),
                    "doc_id": doc_id,
                    "doc_name": doc_name,
                    "doc_date": doc_date,
                    "page": page,
                    "text": supp or desc
                })

        has_allergy = [a for a in allergy_records if a["type"] == "has_allergy"]
        no_allergy = [a for a in allergy_records if a["type"] == "no_allergies"]

        if has_allergy and no_allergy:
            a1 = has_allergy[0]
            a2 = no_allergy[0]
            conflicts.append({
                "event_type": "allergy_discrepancy",
                "conflicting_item": "Penicillin Allergy Documentation",
                "description": f"Potential allergy conflict detected: Document '{a1['doc_name']}' documents Penicillin allergy, while Document '{a2['doc_name']}' documents 'No Known Drug Allergies / None Recorded'.",
                "related_event_ids": [a1["event_id"], a2["event_id"]],
                "source_a_doc_id": a1["doc_id"],
                "source_a_doc_name": a1["doc_name"],
                "source_a_date": a1["doc_date"],
                "source_a_page": a1["page"],
                "source_a_text": a1["text"],
                "source_b_doc_id": a2["doc_id"],
                "source_b_doc_name": a2["doc_name"],
                "source_b_date": a2["doc_date"],
                "source_b_page": a2["page"],
                "source_b_text": a2["text"],
                "status": "unresolved",
                "review_reason": "Severe adverse event risk: Failure to reconcile penicillin allergy documentation could lead to inadvertent beta-lactam exposure in acute settings.",
                "human_action_guidance": "Conflict detected — human review required. Do NOT assume either statement is true without direct clinician verification with the patient or primary provider."
            })

        return conflicts
