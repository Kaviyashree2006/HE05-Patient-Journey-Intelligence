from app.document_processing.classifier import DocumentClassifier


def test_classify_lab_report():
    text = "Comprehensive Metabolic Panel Fasting Blood Glucose 210 mg/dL Hemoglobin A1c 9.4% Reference Interval"
    doc_type, conf = DocumentClassifier.classify(text, "01_Initial_Lab_Report.pdf")
    assert doc_type == "lab_report"
    assert conf > 0.6


def test_classify_prescription():
    text = "Outpatient Prescription Order Rx Lisinopril 10 mg Sig 1 tablet daily Dispense 90 Refills 3"
    doc_type, conf = DocumentClassifier.classify(text, "03_Prescription.pdf")
    assert doc_type == "prescription"
    assert conf > 0.6


def test_classify_clinical_note():
    text = "Chief Complaint History of Present Illness Assessment and Plan Clinical Consultation Note"
    doc_type, conf = DocumentClassifier.classify(text, "02_Consult_Note.pdf")
    assert doc_type == "clinical_note"
    assert conf > 0.6


def test_classify_imaging_report():
    text = "Diagnostic Radiology Examination Bilateral Renal Ultrasound Findings Impression No hydronephrosis"
    doc_type, conf = DocumentClassifier.classify(text, "04_Ultrasound.pdf")
    assert doc_type == "imaging_report"
    assert conf > 0.6


def test_classify_discharge_summary():
    text = "Inpatient Hospital Discharge Summary Admission Date 2026-08-14 Discharge Date 2026-08-19 Hospital Course Disposition"
    doc_type, conf = DocumentClassifier.classify(text, "05_Discharge_Summary.pdf")
    assert doc_type == "discharge_summary"
    assert conf > 0.6
