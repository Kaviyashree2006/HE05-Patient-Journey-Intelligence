import pytest
from app.services.decision_chain_engine import DecisionChainEngine


def test_decision_chain_construction():
    events = [
        {"event_id": "e1", "source_document_id": "d1", "event_type": "test", "event_date": "2026-01-10", "event_description": "Hemoglobin A1c: 9.4 %", "supporting_text": "HbA1c 9.4%"},
        {"event_id": "e2", "source_document_id": "d2", "event_type": "condition", "event_date": "2026-01-15", "event_description": "Type 2 Diabetes Mellitus - newly diagnosed", "supporting_text": "T2DM uncontrolled"},
        {"event_id": "e3", "source_document_id": "d2", "event_type": "medication", "event_date": "2026-01-15", "event_description": "Prescribed Metformin 500 mg daily", "supporting_text": "Metformin 500mg daily"},
        {"event_id": "e4", "source_document_id": "d3", "event_type": "medication", "event_date": "2026-02-18", "event_description": "Prescribed Metformin 1000 mg twice daily", "supporting_text": "Metformin 1000mg BID"},
        {"event_id": "e5", "source_document_id": "d5", "event_type": "condition", "event_date": "2026-08-14", "event_description": "Acute Kidney Injury superimposed on baseline diabetic nephropathy", "supporting_text": "AKI creatinine 2.4"},
        {"event_id": "e6", "source_document_id": "d5", "event_type": "medication", "event_date": "2026-08-19", "event_description": "Prescribed Insulin Glargine 18 units", "supporting_text": "Insulin Glargine 18 units"}
    ]
    documents = [
        {"document_id": "d1", "filename": "01_lab.pdf"},
        {"document_id": "d2", "filename": "02_consult.pdf"},
        {"document_id": "d3", "filename": "03_rx.pdf"},
        {"document_id": "d5", "filename": "05_discharge.pdf"}
    ]

    chains = DecisionChainEngine.construct_chains(events, [], documents)
    assert len(chains) >= 1
    glycemic_chain = next((c for c in chains if "glycemic" in c["chain_title"].lower()), None)
    assert glycemic_chain is not None
    assert len(glycemic_chain["nodes"]) >= 4

    # Verify each node contains evidence grounding and explanation
    for node in glycemic_chain["nodes"]:
        assert node["event_id"] is not None
        assert node["description"]
        assert node["supporting_text"]
        assert node["source_document_name"]
