import pytest
from app.services.priority_engine import PriorityEngine


def test_priority_critical_events():
    # AKI
    p, reason = PriorityEngine.evaluate_priority({
        "event_type": "condition",
        "event_description": "Acute Kidney Injury superimposed on diabetic nephropathy",
        "supporting_text": "Serum Creatinine on admission was 2.4 mg/dL (Acute Kidney Injury)"
    })
    assert p == "Critical"
    assert "renal" in reason.lower()

    # Hospital admission
    p, reason = PriorityEngine.evaluate_priority({
        "event_type": "admission",
        "event_description": "Inpatient Hospital Admission",
        "supporting_text": "The patient presented with acute viral gastroenteritis, persistent emesis, and volume depletion."
    })
    assert p == "Critical"

    # Severe Penicillin allergy
    p, reason = PriorityEngine.evaluate_priority({
        "event_type": "allergy",
        "event_description": "Severe Penicillin Allergy with angioedema",
        "supporting_text": "Allergies: Penicillin (severe urticaria and facial angioedema)"
    })
    assert p == "Critical"
    assert "safety" in reason.lower()

    # Metformin safety hold
    p, reason = PriorityEngine.evaluate_priority({
        "event_type": "treatment",
        "event_description": "Metformin held temporarily due to recent acute kidney injury",
        "supporting_text": "Metformin held temporarily due to recent acute kidney injury; do not resume until renal recheck"
    })
    assert p == "Critical"
    assert "hold" in reason.lower() or "acidosis" in reason.lower()


def test_priority_high_events():
    # Markedly elevated HbA1c
    p, reason = PriorityEngine.evaluate_priority({
        "event_type": "test",
        "event_description": "Hemoglobin A1c: 9.4 %",
        "supporting_text": "Hemoglobin A1c 9.4 % HIGH 4.0 - 5.6"
    })
    assert p == "High"
    assert "hyperglycemia" in reason.lower() or "glycated" in reason.lower()

    # T2D Diagnosis
    p, reason = PriorityEngine.evaluate_priority({
        "event_type": "condition",
        "event_description": "Type 2 Diabetes Mellitus - newly diagnosed",
        "supporting_text": "Type 2 Diabetes Mellitus - newly diagnosed, uncontrolled"
    })
    assert p == "High"

    # Insulin initiation
    p, reason = PriorityEngine.evaluate_priority({
        "event_type": "medication",
        "event_description": "Prescribed Insulin Glargine 18 units",
        "supporting_text": "Prescribed Insulin Glargine 18 units subcutaneous daily at bedtime"
    })
    assert p == "High"
    assert "insulin" in reason.lower()


def test_priority_moderate_and_informational_events():
    # Routine Lisinopril
    p, reason = PriorityEngine.evaluate_priority({
        "event_type": "medication",
        "event_description": "Prescribed Lisinopril 10 mg daily",
        "supporting_text": "Prescribed Lisinopril 10 mg daily for renal protection"
    })
    assert p == "Moderate"

    # Renal ultrasound
    p, reason = PriorityEngine.evaluate_priority({
        "event_type": "procedure",
        "event_description": "Renal Ultrasound Examination",
        "supporting_text": "Study: Bilateral Renal Ultrasound Examination"
    })
    assert p == "Moderate"

    # Normal baseline finding
    p, reason = PriorityEngine.evaluate_priority({
        "event_type": "test",
        "event_description": "Left Kidney Length: 10.6 cm normal",
        "supporting_text": "Left Kidney: Measures 10.6 cm in length. Normal echogenicity."
    })
    assert p in ["Moderate", "Informational"]
