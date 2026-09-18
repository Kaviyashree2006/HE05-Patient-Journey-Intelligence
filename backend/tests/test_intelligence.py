import pytest
from app.ai.rule_extractor import ClinicalRuleExtractor
from app.services.temporal_engine import TemporalEngine
from app.services.relationship_engine import RelationshipEngine
from app.services.change_detector import ChangeDetector
from app.services.conflict_detector import ConflictDetector
from app.services.gap_detector import GapDetector
from app.services.qa_engine import QAEngine
from app.services.milestone_engine import MilestoneEngine
from app.services.decision_chain_engine import DecisionChainEngine


def test_rule_extraction():
    text = """
    Patient Name: Sarah Jenkins
    Patient ID: PAT-2026-0814
    Report Date: 2026-01-10
    Hemoglobin A1c: 9.4 % (HIGH)
    Fasting Blood Glucose: 210 mg/dL (HIGH)
    Serum Creatinine: 1.1 mg/dL
    eGFR: 72 mL/min
    """
    res = ClinicalRuleExtractor.extract(text, "lab.pdf", "lab_report")
    assert res.document_type == "lab_report"
    assert res.document_date == "2026-01-10"
    assert res.patient_reference == "PAT-2026-0814"
    assert len(res.events) >= 3

    # Verify supporting text is present for all events
    for ev in res.events:
        assert ev.supporting_text
        assert ev.event_date == "2026-01-10"
        assert ev.event_date_type == "explicit"


def test_temporal_engine():
    events = [
        {"event_id": "1", "event_date": "2026-08-19", "event_date_type": "explicit", "event_description": "Discharge"},
        {"event_id": "2", "event_date": "2026-01-10", "event_date_type": "explicit", "event_description": "Lab Test"},
        {"event_id": "3", "event_date": "2026-02-18", "event_date_type": "explicit", "event_description": "Prescription"},
        {"event_id": "4", "event_date": None, "event_date_type": "unknown", "event_description": "Undated note"}
    ]
    sorted_ev = TemporalEngine.sort_events_chronologically(events)
    assert sorted_ev[0]["event_id"] == "2"  # 2026-01-10
    assert sorted_ev[1]["event_id"] == "3"  # 2026-02-18
    assert sorted_ev[2]["event_id"] == "1"  # 2026-08-19
    assert sorted_ev[3]["event_id"] == "4"  # undated at end


def test_relationship_engine():
    events = [
        {"event_id": "e1", "event_type": "test", "event_description": "Hemoglobin A1c: 9.4 %"},
        {"event_id": "e2", "event_type": "condition", "event_description": "Type 2 Diabetes Mellitus"},
        {"event_id": "e3", "event_type": "medication", "event_description": "Medication Prescribed: Metformin 500 mg"}
    ]
    rels = RelationshipEngine.discover_relationships(events)
    assert len(rels) >= 2
    types = [r["relationship_type"] for r in rels]
    assert "resulted_in" in types


def test_change_detector_medication():
    """TEST 4: Medication change detection continues to work."""
    events = [
        {"event_id": "m1", "event_type": "medication", "event_date": "2026-01-15", "event_description": "Medication Prescribed: Metformin 500 mg daily", "supporting_text": "Metformin 500mg"},
        {"event_id": "m2", "event_type": "medication", "event_date": "2026-02-18", "event_description": "Medication Increased: Metformin 1000 mg twice daily", "supporting_text": "Metformin 1000mg"}
    ]
    changes = ChangeDetector.detect_changes(events)
    assert len(changes) >= 1
    assert changes[0]["item_name"] == "Metformin"
    assert changes[0]["change_type"] == "medication_change"
    assert changes[0]["significance_category"] == "medication_dose_increased"


def test_test1_serum_creatinine_not_grouped_with_urine_acr():
    """TEST 1: Serum Creatinine must NOT be grouped with Urine Albumin/Creatinine Ratio."""
    events = [
        {
            "event_id": "e1",
            "event_type": "test",
            "event_date": "2026-01-10",
            "event_description": "Serum Creatinine Test: 1.1 mg/dL (NORMAL)",
            "supporting_text": "Serum Creatinine 1.1 NORMAL 0.5 - 1.2 mg/dL"
        },
        {
            "event_id": "e2",
            "event_type": "test",
            "event_date": "2026-02-18",
            "event_description": "Urine Albumin/Creatinine Ratio Test: 65 mg/g (ELEVATED)",
            "supporting_text": "Urine Albumin/Creatinine 65 HIGH < 30 mg/g"
        }
    ]
    changes = ChangeDetector.detect_changes(events)
    # Must NOT generate a longitudinal trajectory comparing Serum Creatinine against Urine ACR
    assert len(changes) == 0
    assert not any(c.get("item_name") == "Creatinine" for c in changes)


def test_test2_serum_creatinine_repeated_measurement_trajectory():
    """TEST 2: A valid repeated Serum Creatinine measurement across different dates can generate a comparison."""
    events = [
        {
            "event_id": "e1",
            "event_type": "test",
            "event_date": "2026-01-10",
            "event_description": "Serum Creatinine Test: 1.1 mg/dL (NORMAL)",
            "supporting_text": "Serum Creatinine 1.1 NORMAL 0.5 - 1.2 mg/dL"
        },
        {
            "event_id": "e2",
            "event_type": "test",
            "event_date": "2026-08-14",
            "event_description": "Serum Creatinine Test: 2.4 mg/dL (ELEVATED)",
            "supporting_text": "Serum Creatinine 2.4 mg/dL on hospital admission"
        }
    ]
    changes = ChangeDetector.detect_changes(events)
    assert len(changes) == 1
    chg = changes[0]
    assert chg["item_name"] == "Serum Creatinine"
    assert chg["change_type"] == "lab_trajectory"
    assert chg["significance_category"] == "lab_value_increased"
    assert chg["previous_date"] == "2026-01-10"
    assert chg["new_date"] == "2026-08-14"
    assert "1.1" in chg["previous_value"]
    assert "2.4" in chg["new_value"]


def test_test3_same_day_unrelated_lab_measurements_no_trajectory():
    """TEST 3: Same-day unrelated laboratory measurements do not become a longitudinal trajectory."""
    events = [
        {
            "event_id": "e1",
            "event_type": "test",
            "event_date": "2026-01-10",
            "event_description": "Serum Creatinine Test: 1.1 mg/dL (NORMAL)",
            "supporting_text": "Serum Creatinine 1.1 mg/dL"
        },
        {
            "event_id": "e2",
            "event_type": "test",
            "event_date": "2026-01-10",
            "event_description": "Fasting Blood Glucose Test: 210 mg/dL (ELEVATED)",
            "supporting_text": "Fasting Blood Glucose 210 mg/dL"
        },
        {
            "event_id": "e3",
            "event_type": "test",
            "event_date": "2026-01-10",
            "event_description": "HbA1c Glycated Hemoglobin Test: 9.4 % (ELEVATED)",
            "supporting_text": "Hemoglobin A1c 9.4 %"
        },
        {
            "event_id": "e4",
            "event_type": "test",
            "event_date": "2026-01-10",
            "event_description": "Serum Creatinine Test: 1.1 mg/dL (NORMAL)",
            "supporting_text": "Repeat verification same day"
        }
    ]
    changes = ChangeDetector.detect_changes(events)
    # All are on the same day 2026-01-10, so no longitudinal changes should be generated
    assert len(changes) == 0


def test_conflict_detector():
    """TEST 5: Existing conflict detection continues to work."""
    events = [
        {"event_id": "e1", "source_document_id": "d1", "event_description": "Allergies: Penicillin (severe urticaria)", "supporting_text": "Allergies: Penicillin"},
        {"event_id": "e2", "source_document_id": "d2", "event_description": "Allergies: No Known Drug Allergies (NKDA)", "supporting_text": "Allergies: NKDA"}
    ]
    docs = [
        {"document_id": "d1", "filename": "doc1.pdf", "original_filename": "Consult.pdf"},
        {"document_id": "d2", "filename": "doc2.pdf", "original_filename": "Discharge.pdf"}
    ]
    conflicts = ConflictDetector.detect_conflicts(events, docs)
    assert len(conflicts) == 1
    assert conflicts[0]["event_type"] == "allergy_discrepancy"
    assert "Penicillin" in conflicts[0]["description"]


def test_gap_detector():
    """TEST 6: Existing gap detection continues to work."""
    events = [
        {"event_id": "e1", "event_date": "2026-05-12", "event_description": "Renal Ultrasound"},
        {"event_id": "e2", "event_date": "2026-08-14", "event_description": "Hospital Admission"}
    ]
    gaps = GapDetector.detect_gaps(events)
    assert len(gaps) == 1
    assert gaps[0]["days_gap"] >= 90
    assert "gap detected" in gaps[0]["description"]


def test_qa_engine():
    """TEST 9: Existing evidence-grounded Q&A continues to work."""
    import asyncio
    events = [
        {"event_id": "e1", "source_document_id": "d1", "event_type": "medication", "event_date": "2026-01-15", "event_description": "Prescribed Metformin 500 mg daily", "supporting_text": "Prescribed Metformin 500 mg daily"}
    ]
    docs = [{"document_id": "d1", "filename": "02_Consult.pdf", "original_filename": "02_Consult.pdf", "document_type": "clinical_note"}]

    resp = asyncio.run(QAEngine.answer_question("When was Metformin first prescribed?", events, docs))
    assert resp.has_sufficient_evidence is True
    assert "2026-01-15" in resp.answer
    assert len(resp.citations) >= 1

    resp_unk = asyncio.run(QAEngine.answer_question("Has the patient had a brain MRI?", events, docs))
    assert resp_unk.has_sufficient_evidence is False
    assert "could not find sufficient evidence" in resp_unk.answer.lower()


def test_milestone_detection():
    """TEST 7: Existing milestone detection continues to work."""
    events = [
        {"event_id": "ev1", "source_document_id": "doc1", "event_type": "test", "event_date": "2026-01-10", "event_description": "HbA1c Glycated Hemoglobin Test: 9.4 %", "supporting_text": "Metabolic panel: HbA1c 9.4 %", "source_page": 1},
        {"event_id": "ev2", "source_document_id": "doc2", "event_type": "condition", "event_date": "2026-01-15", "event_description": "Type 2 Diabetes Mellitus - newly diagnosed", "supporting_text": "Endocrinology Consult: Type 2 Diabetes Mellitus newly diagnosed", "source_page": 1}
    ]
    docs = [
        {"document_id": "doc1", "filename": "01_lab.pdf"},
        {"document_id": "doc2", "filename": "02_consult.pdf"}
    ]
    milestones = MilestoneEngine.extract_milestones(events, docs)
    assert len(milestones) >= 2


def test_action_chain_detection():
    """TEST 8: Existing action-chain detection continues to work."""
    events = [
        {"event_id": "e1", "source_document_id": "d1", "event_type": "test", "event_date": "2026-01-10", "event_description": "Hemoglobin A1c: 9.4 %", "supporting_text": "HbA1c 9.4%"},
        {"event_id": "e2", "source_document_id": "d2", "event_type": "condition", "event_date": "2026-01-15", "event_description": "Type 2 Diabetes Mellitus - newly diagnosed", "supporting_text": "T2DM"},
        {"event_id": "e3", "source_document_id": "d2", "event_type": "medication", "event_date": "2026-01-15", "event_description": "Prescribed Metformin 500 mg daily", "supporting_text": "Metformin 500mg"}
    ]
    docs = [
        {"document_id": "d1", "filename": "01_lab.pdf"},
        {"document_id": "d2", "filename": "02_consult.pdf"}
    ]
    chains = DecisionChainEngine.construct_chains(events, [], docs)
    assert len(chains) >= 1



