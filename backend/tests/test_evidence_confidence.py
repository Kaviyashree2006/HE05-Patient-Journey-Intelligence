import pytest
from app.services.evidence_confidence_engine import EvidenceConfidenceEngine


def test_strong_evidence_numerical_lab():
    level, rationale = EvidenceConfidenceEngine.evaluate_confidence({
        "event_type": "test",
        "event_date_type": "explicit",
        "event_description": "Hemoglobin A1c: 9.4 %",
        "supporting_text": "Hemoglobin A1c 9.4 % HIGH 4.0 - 5.6 %"
    })
    assert level == "Strong"
    assert "quantitative" in rationale.lower() or "numerical" in rationale.lower()


def test_strong_evidence_formal_prescription():
    level, rationale = EvidenceConfidenceEngine.evaluate_confidence({
        "event_type": "medication",
        "event_date_type": "explicit",
        "event_description": "Prescribed Metformin 500 mg daily",
        "supporting_text": "Prescribed Metformin 500 mg daily with dinner."
    })
    assert level == "Strong"
    assert "prescription" in rationale.lower() or "formulation" in rationale.lower()


def test_moderate_evidence_clinical_consult():
    level, rationale = EvidenceConfidenceEngine.evaluate_confidence({
        "event_type": "condition",
        "event_date_type": "explicit",
        "event_description": "Type 2 Diabetes Mellitus - newly diagnosed",
        "supporting_text": "1. Type 2 Diabetes Mellitus - newly diagnosed, uncontrolled."
    })
    assert level in ["Strong", "Moderate"]
    assert len(rationale) > 10


def test_limited_evidence_approximate_subjective_recall():
    level, rationale = EvidenceConfidenceEngine.evaluate_confidence({
        "event_type": "symptom",
        "event_date_type": "relative",
        "event_description": "Polyuria, polydipsia, and fatigue",
        "supporting_text": "Patient reports polyuria, polydipsia, and fatigue over past 4 weeks."
    })
    assert level == "Limited"
    assert "relative" in rationale.lower() or "subjective" in rationale.lower()
