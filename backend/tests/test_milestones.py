import pytest
from app.services.milestone_engine import MilestoneEngine


def test_milestone_extraction():
    events = [
        {
            "event_id": "ev1",
            "source_document_id": "doc1",
            "event_type": "test",
            "event_date": "2026-01-10",
            "event_description": "Hemoglobin A1c: 9.4 %",
            "supporting_text": "Metabolic panel: Hemoglobin A1c 9.4 %",
            "source_page": 1
        },
        {
            "event_id": "ev2",
            "source_document_id": "doc2",
            "event_type": "condition",
            "event_date": "2026-01-15",
            "event_description": "Type 2 Diabetes Mellitus - newly diagnosed",
            "supporting_text": "Endocrinology Consult: Type 2 Diabetes Mellitus newly diagnosed",
            "source_page": 1
        },
        {
            "event_id": "ev3",
            "source_document_id": "doc2",
            "event_type": "medication",
            "event_date": "2026-01-15",
            "event_description": "Prescribed Metformin 500 mg daily",
            "supporting_text": "Prescribed Metformin 500 mg daily with dinner.",
            "source_page": 1
        },
        {
            "event_id": "ev4",
            "source_document_id": "doc3",
            "event_type": "medication",
            "event_date": "2026-02-18",
            "event_description": "Prescribed Metformin 1000 mg twice daily",
            "supporting_text": "Dose increased from 500mg daily due to postprandial glucose levels.",
            "source_page": 1
        }
    ]
    documents = [
        {"document_id": "doc1", "filename": "01_lab.pdf"},
        {"document_id": "doc2", "filename": "02_consult.pdf"},
        {"document_id": "doc3", "filename": "03_rx.pdf"}
    ]

    milestones = MilestoneEngine.extract_milestones(events, documents)
    assert len(milestones) >= 3

    types = [m["milestone_type"] for m in milestones]
    assert "diagnostic_investigation" in types
    assert "clinical_consultation" in types
    assert "treatment_initiation" in types

    for m in milestones:
        assert m["event_id"] is not None
        assert m["document_id"] is not None
        assert m["title"]
        assert m["supporting_text"]
        assert m["source_page"] == 1
