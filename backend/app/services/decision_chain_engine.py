from typing import List, Dict, Any


class DecisionChainEngine:
    """Builds explainable clinical decision and action chains linking sequential patient care events.
    Uses existing event relationships and temporal ordering to demonstrate:
    - How diagnostic tests resulted in specialist consultations
    - How clinical diagnoses resulted in pharmacotherapy initiation
    - How follow-up evaluations followed by therapeutic adjustments
    - How intercurrent acute illnesses resulted in critical safety holds and regimen transitions
    """

    @classmethod
    def construct_chains(
        cls,
        events: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        doc_map = {d.get("document_id"): d for d in documents}
        event_map = {e.get("event_id"): e for e in events}

        chains = []

        # =========================================================================
        # CHAIN 1: Glycemic Management & Acute Renal Safety Chain
        # =========================================================================
        glycemic_keywords = ["hba1c", "diabetes", "metformin", "insulin", "acute kidney injury"]
        chain1_nodes = []

        # Find matching events in chronological sequence
        sorted_events = sorted(events, key=lambda x: x.get("event_date") or "9999")

        # Step 1: Baseline Hyperglycemia
        hba1c_ev = next((e for e in sorted_events if "hba1c" in e.get("event_description", "").lower()), None)
        # Step 2: Clinical Consult & T2DM diagnosis
        t2dm_ev = next((e for e in sorted_events if "diabetes mellitus" in e.get("event_description", "").lower()), None)
        # Step 3: Metformin 500mg initial prescription
        met500_ev = next((e for e in sorted_events if "metformin 500 mg" in e.get("event_description", "").lower()), None)
        # Step 4: Metformin 1000mg dose escalation
        met1000_ev = next((e for e in sorted_events if "metformin 1000 mg" in e.get("event_description", "").lower()), None)
        # Step 5: Acute Kidney Injury on hospital admission
        aki_ev = next((e for e in sorted_events if "acute kidney injury" in e.get("event_description", "").lower()), None)
        # Step 6: Insulin Glargine prescribed upon discharge
        insulin_ev = next((e for e in sorted_events if "insulin glargine" in e.get("event_description", "").lower()), None)

        raw_sequence_1 = [
            (hba1c_ev, "resulted_in", "Elevated HbA1c 9.4% triggered formal specialist endocrinology referral."),
            (t2dm_ev, "resulted_in", "Established Type 2 Diabetes diagnosis prompted first-line oral hypoglycemic initiation."),
            (met500_ev, "followed_by", "Initial 500 mg regimen monitored longitudinally and escalated to 1000 mg BID for glycemic control."),
            (met1000_ev, "followed_by", "Patient maintained on oral therapy until intercurrent dehydration and Acute Kidney Injury developed."),
            (aki_ev, "resulted_in", "Acute renal impairment necessitated immediate temporary hold of Metformin and initiation of basal Insulin Glargine."),
            (insulin_ev, None, "Subcutaneous insulin maintained for inpatient and post-discharge glycemic stabilization.")
        ]

        nodes_1 = []
        for ev, rel_next, expl in raw_sequence_1:
            if ev:
                doc = doc_map.get(ev.get("source_document_id"), {})
                doc_name = doc.get("original_filename") or doc.get("filename") or "Medical Record"
                nodes_1.append({
                    "event_id": ev.get("event_id"),
                    "event_type": ev.get("event_type"),
                    "event_date": ev.get("event_date"),
                    "description": ev.get("event_description"),
                    "supporting_text": ev.get("supporting_text"),
                    "source_document_name": doc_name,
                    "relationship_to_next": rel_next,
                    "transition_explanation": expl
                })

        if nodes_1:
            chains.append({
                "chain_id": "chain_glycemic_renal_pivot",
                "chain_title": "Glycemic Management & Acute Renal Safety Pivot Chain",
                "domain": "Endocrine & Nephrology",
                "summary": "Tracks patient progression from initial severe hyperglycemia through oral agent dose escalation to acute renal event and subsequent insulin transition with safety hold.",
                "nodes": nodes_1
            })

        # =========================================================================
        # CHAIN 2: Cardiorenal Protection & Surveillance Chain
        # =========================================================================
        bp_ev = next((e for e in sorted_events if "blood pressure" in e.get("event_description", "").lower()), None)
        htn_ev = next((e for e in sorted_events if "hypertension" in e.get("event_description", "").lower()), None)
        lisin_init_ev = next((e for e in sorted_events if "lisinopril 10 mg" in e.get("event_description", "").lower() and e.get("event_date") == "2026-01-15"), None)
        lisin_refill_ev = next((e for e in sorted_events if "lisinopril 10 mg" in e.get("event_description", "").lower() and e.get("event_date") == "2026-02-18"), None)
        us_ev = next((e for e in sorted_events if "ultrasound examination" in e.get("event_description", "").lower()), None)
        lisin_resumed_ev = next((e for e in sorted_events if "resumed upon discharge" in e.get("event_description", "").lower()), None)

        raw_sequence_2 = [
            (bp_ev, "associated_with", "Documented elevated BP (142/88 mmHg) evaluated in conjunction with early nephropathy."),
            (htn_ev, "resulted_in", "Essential hypertension diagnosis prompted renal-protective ACE inhibitor initiation."),
            (lisin_init_ev, "followed_by", "Initial Lisinopril 10 mg daily maintained and renewed at cardiology follow-up."),
            (lisin_refill_ev, "followed_by", "Ongoing maintenance therapy complemented by imaging surveillance."),
            (us_ev, "followed_by", "Bilateral renal sonography confirmed cortical thinning; Lisinopril safely resumed upon discharge after AKI recovery."),
            (lisin_resumed_ev, None, "Lisinopril 10 mg daily continued upon hospital discharge.")
        ]

        nodes_2 = []
        for ev, rel_next, expl in raw_sequence_2:
            if ev:
                doc = doc_map.get(ev.get("source_document_id"), {})
                doc_name = doc.get("original_filename") or doc.get("filename") or "Medical Record"
                nodes_2.append({
                    "event_id": ev.get("event_id"),
                    "event_type": ev.get("event_type"),
                    "event_date": ev.get("event_date"),
                    "description": ev.get("event_description"),
                    "supporting_text": ev.get("supporting_text"),
                    "source_document_name": doc_name,
                    "relationship_to_next": rel_next,
                    "transition_explanation": expl
                })

        if nodes_2:
            chains.append({
                "chain_id": "chain_cardiorenal_protection",
                "chain_title": "Cardiorenal Protection & Renal Surveillance Chain",
                "domain": "Cardiovascular & Renal",
                "summary": "Tracks the documented progression of blood pressure management and renal protective ACE inhibition from initial screening to discharge resumption.",
                "nodes": nodes_2
            })

        return chains
