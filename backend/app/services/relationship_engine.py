import json
from typing import List, Dict, Any


class RelationshipEngine:
    """Discovers supported clinical relationships between medical events.
    Does not make speculative causal claims; links grounded sequences."""

    @classmethod
    def discover_relationships(cls, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        relationships = []
        seen_pairs = set()

        def add_rel(source_id: str, target_id: str, rel_type: str, confidence: float, explanation: str):
            pair_key = (source_id, target_id, rel_type)
            if pair_key not in seen_pairs and source_id != target_id:
                seen_pairs.add(pair_key)
                relationships.append({
                    "source_event_id": source_id,
                    "target_event_id": target_id,
                    "relationship_type": rel_type,
                    "confidence": confidence,
                    "explanation": explanation
                })

        # Categorize events by type
        tests = [e for e in events if e.get("event_type") == "test"]
        conditions = [e for e in events if e.get("event_type") == "condition"]
        medications = [e for e in events if e.get("event_type") == "medication"]
        procedures = [e for e in events if e.get("event_type") == "procedure"]
        findings = [e for e in events if e.get("event_type") == "clinical_finding"]
        discharges = [e for e in events if e.get("event_type") == "discharge"]

        # 1. Test -> Finding / Condition (e.g. HbA1c test -> Diabetes condition)
        for t in tests:
            t_desc = t.get("event_description", "").lower()
            for c in conditions:
                c_desc = c.get("event_description", "").lower()
                if "hba1c" in t_desc or "a1c" in t_desc or "glucose" in t_desc:
                    if "diabetes" in c_desc or "t2dm" in c_desc:
                        add_rel(
                            t["event_id"], c["event_id"], "resulted_in", 0.95,
                            f"Glycemic laboratory evaluation supported clinical diagnosis of {c.get('event_description')}"
                        )
                if "creatinine" in t_desc or "egfr" in t_desc:
                    if "nephropathy" in c_desc or "kidney" in c_desc:
                        add_rel(
                            t["event_id"], c["event_id"], "associated_with", 0.92,
                            f"Renal function marker correlates with {c.get('event_description')}"
                        )
                if "blood pressure" in t_desc:
                    if "hypertension" in c_desc:
                        add_rel(
                            t["event_id"], c["event_id"], "associated_with", 0.94,
                            f"Blood pressure measurement documented in context of {c.get('event_description')}"
                        )

        # 2. Condition -> Medication (Treatment for)
        for c in conditions:
            c_desc = c.get("event_description", "").lower()
            for m in medications:
                m_desc = m.get("event_description", "").lower()
                if ("diabetes" in c_desc or "t2dm" in c_desc) and ("metformin" in m_desc or "insulin" in m_desc):
                    add_rel(
                        c["event_id"], m["event_id"], "resulted_in", 0.95,
                        f"Documented condition {c.get('event_description')} prompted antidiabetic medication management"
                    )
                if "hypertension" in c_desc and ("lisinopril" in m_desc or "amlodipine" in m_desc):
                    add_rel(
                        c["event_id"], m["event_id"], "resulted_in", 0.95,
                        f"Hypertension diagnosis prompted antihypertensive prescription ({m.get('event_description')})"
                    )

        # 3. Procedure -> Finding (e.g., Renal Ultrasound -> Cortical thinning)
        for p in procedures:
            p_desc = p.get("event_description", "").lower()
            for f in findings:
                f_desc = f.get("event_description", "").lower()
                if "ultrasound" in p_desc or "imaging" in p_desc:
                    if "radiological" in f_desc or "renal" in f_desc or "cortical" in f_desc or "kidney" in f_desc:
                        add_rel(
                            p["event_id"], f["event_id"], "resulted_in", 0.98,
                            "Imaging procedure yielded specific radiological findings"
                        )

        # 4. Procedure (Admission) -> Discharge
        for p in procedures:
            if "admission" in p.get("event_description", "").lower():
                for d in discharges:
                    add_rel(
                        p["event_id"], d["event_id"], "followed_by", 0.99,
                        "Inpatient hospital admission followed by formal discharge disposition"
                    )

        # 5. Medication -> Monitoring / Adjustment
        # If multiple medications of same agent exist across dates
        med_by_name: Dict[str, List[Dict[str, Any]]] = {}
        for m in medications:
            desc = m.get("event_description", "").lower()
            for name in ["metformin", "lisinopril", "insulin"]:
                if name in desc:
                    med_by_name.setdefault(name, []).append(m)

        for name, m_list in med_by_name.items():
            if len(m_list) > 1:
                # Sort by date
                sorted_m = sorted(m_list, key=lambda x: x.get("event_date") or "9999")
                for i in range(len(sorted_m) - 1):
                    add_rel(
                        sorted_m[i]["event_id"], sorted_m[i+1]["event_id"], "followed_by", 0.95,
                        f"Longitudinal adjustment of {name.capitalize()} therapy over time"
                    )

        return relationships
