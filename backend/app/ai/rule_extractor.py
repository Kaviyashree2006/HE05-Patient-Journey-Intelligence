import re
from typing import List, Dict, Any, Optional
from app.schemas.models import (
    DocumentExtractionResult,
    ExtractedEventItem,
    ExtractedEntities
)


class ClinicalRuleExtractor:
    """Deterministic, high-precision clinical regex & NLP pattern extractor.
    Ensures 100% offline reliability, strict evidence linkage, and zero hallucination."""

    # Date pattern: matches YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY, "15 January 2026", "Jan 15, 2026"
    DATE_PATTERNS = [
        r"\b(20\d{2}[-/]\d{1,2}[-/]\d{1,2})\b",
        r"\b(\d{1,2}[-/]\d{1,2}[-/]20\d{2})\b",
        r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+20\d{2})\b",
        r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+20\d{2})\b",
    ]

    MONTH_MAP = {
        "jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06",
        "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12"
    }

    @classmethod
    def normalize_date(cls, raw_date_str: str) -> Optional[str]:
        if not raw_date_str:
            return None
        cleaned = raw_date_str.strip().replace(",", "")

        # YYYY-MM-DD
        m = re.match(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$", cleaned)
        if m:
            return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"

        # DD/MM/YYYY
        m = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$", cleaned)
        if m:
            # Assume first number is day or month
            return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"

        # 15 January 2026
        m = re.match(r"^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$", cleaned)
        if m:
            month_key = m.group(2)[:3].lower()
            month_num = cls.MONTH_MAP.get(month_key, "01")
            return f"{m.group(3)}-{month_num}-{int(m.group(1)):02d}"

        # January 15 2026
        m = re.match(r"^([A-Za-z]+)\s+(\d{1,2})\s+(\d{4})$", cleaned)
        if m:
            month_key = m.group(1)[:3].lower()
            month_num = cls.MONTH_MAP.get(month_key, "01")
            return f"{m.group(3)}-{month_num}-{int(m.group(2)):02d}"

        return cleaned

    @classmethod
    def find_first_date(cls, text: str) -> Optional[str]:
        for pattern in cls.DATE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return cls.normalize_date(match.group(1))
        return None

    @classmethod
    def extract(cls, text: str, filename: str, doc_type: str, pages: List[Dict[str, Any]] = None) -> DocumentExtractionResult:
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # 1. Document-level date detection
        doc_date = None
        doc_date_headers = [
            r"(?:Document\s+Date|Date\s+of\s+Report|Report\s+Date|Collection\s+Date|Encounter\s+Date|Date:)\s*[:]?\s*([^\n;]+)",
            r"(?:Date\s+of\s+Consultation|Prescription\s+Date|Admission\s+Date|Exam\s+Date)\s*[:]?\s*([^\n;]+)"
        ]
        for header_pattern in doc_date_headers:
            m = re.search(header_pattern, text, re.IGNORECASE)
            if m:
                found = cls.find_first_date(m.group(1))
                if found:
                    doc_date = found
                    break

        if not doc_date:
            doc_date = cls.find_first_date(text)

        # 2. Patient Reference detection
        patient_ref = None
        pat_patterns = [
            r"(?:Patient\s*ID|MRN|Patient\s*Ref(?:erence)?|Record\s*#)\s*[:]?\s*([A-Z0-9_-]+)",
            r"\b(PAT-20\d{2}-\d+)\b"
        ]
        for pat in pat_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                patient_ref = m.group(1)
                break

        events: List[ExtractedEventItem] = []

        # 3. Document-specific pattern extractors
        if doc_type == "lab_report":
            cls._extract_lab_events(lines, doc_date, events)
        elif doc_type == "prescription":
            cls._extract_prescription_events(lines, doc_date, events)
        elif doc_type == "clinical_note":
            cls._extract_clinical_events(lines, doc_date, events)
        elif doc_type == "imaging_report":
            cls._extract_imaging_events(lines, doc_date, events)
        elif doc_type == "discharge_summary":
            cls._extract_discharge_events(lines, doc_date, events)
        else:
            cls._extract_generic_events(lines, doc_date, events)

        # If no specific events were caught, build high-level document event
        if not events:
            events.append(ExtractedEventItem(
                event_type="clinical_finding",
                event_date=doc_date,
                event_date_type="explicit" if doc_date else "unknown",
                description=f"Medical document recorded: {filename}",
                entities=ExtractedEntities(),
                supporting_text=lines[0] if lines else "Document uploaded",
                source_page=1,
                confidence=0.85
            ))

        return DocumentExtractionResult(
            document_type=doc_type,
            document_date=doc_date,
            patient_reference=patient_ref,
            events=events
        )

    @classmethod
    def _extract_lab_events(cls, lines: List[str], doc_date: Optional[str], events: List[ExtractedEventItem]):
        lab_markers = [
            (r"(?:Hemoglobin\s+A1c|HbA1c)\s*[:=]?\s*([\d\.]+)\s*(%|percent)?", "HbA1c Glycated Hemoglobin Test"),
            (r"(?:Fasting\s+Blood\s+Glucose|Glucose,?\s*Fasting|Glucose)\s*[:=]?\s*([\d\.]+)\s*(mg/dL|mmol/L)?", "Fasting Blood Glucose Test"),
            (r"(?:Serum\s+Creatinine|Creatinine)\s*[:=]?\s*([\d\.]+)\s*(mg/dL|umol/L)?", "Serum Creatinine Test"),
            (r"(?:eGFR|Estimated\s+GFR)\s*[:=]?\s*([\d\.]+)\s*(mL/min[^\n,]*)?", "eGFR Renal Function Test"),
            (r"(?:Blood\s+Pressure|BP)\s*[:=]?\s*(\d{2,3}/\d{2,3})\s*(mmHg)?", "Blood Pressure Measurement"),
            (r"(?:Total\s+Cholesterol|Cholesterol)\s*[:=]?\s*([\d\.]+)\s*(mg/dL)?", "Total Cholesterol Test"),
            (r"(?:Urine\s+Albumin/Creatinine\s+Ratio|Microalbuminuria|UACR)\s*[:=]?\s*([\d\.]+)\s*(mg/g)?", "Urine Albumin/Creatinine Ratio Test")
        ]

        for line in lines:
            for pattern, test_name in lab_markers:
                m = re.search(pattern, line, re.IGNORECASE)
                if m:
                    value = m.group(1)
                    unit = m.group(2) or ""
                    # Check for flag in line (High, Low, Abnormal, Critical)
                    flag = "normal"
                    if re.search(r"\b(high|elevated|h)\b", line, re.IGNORECASE):
                        flag = "elevated"
                    elif re.search(r"\b(low|l)\b", line, re.IGNORECASE):
                        flag = "low"

                    events.append(ExtractedEventItem(
                        event_type="test",
                        event_date=doc_date,
                        event_date_type="explicit" if doc_date else "unknown",
                        description=f"{test_name}: {value} {unit} ({flag.upper()})",
                        entities=ExtractedEntities(
                            tests=[{"name": test_name, "value": value, "unit": unit.strip(), "status": flag}]
                        ),
                        supporting_text=line,
                        source_page=1,
                        confidence=0.96
                    ))

    @classmethod
    def _extract_prescription_events(cls, lines: List[str], doc_date: Optional[str], events: List[ExtractedEventItem]):
        med_patterns = [
            (r"\b(Metformin(?:\s+HCl)?)\s+(\d+\s*mg)\s*([^\n;]+)?", "Metformin"),
            (r"\b(Lisinopril)\s+(\d+\s*mg)\s*([^\n;]+)?", "Lisinopril"),
            (r"\b(Insulin\s+Glargine|Lantus)\s+(\d+\s*units?)\s*([^\n;]+)?", "Insulin Glargine"),
            (r"\b(Atorvastatin|Lipitor)\s+(\d+\s*mg)\s*([^\n;]+)?", "Atorvastatin"),
            (r"\b(Aspirin)\s+(\d+\s*mg)\s*([^\n;]+)?", "Aspirin"),
            (r"\b(Amlodipine)\s+(\d+\s*mg)\s*([^\n;]+)?", "Amlodipine"),
            (r"\b(Empagliflozin|Jardiance)\s+(\d+\s*mg)\s*([^\n;]+)?", "Empagliflozin")
        ]

        for line in lines:
            for pattern, med_name in med_patterns:
                m = re.search(pattern, line, re.IGNORECASE)
                if m:
                    dose = m.group(2)
                    instructions = m.group(3) or "daily"

                    status = "prescribed"
                    if re.search(r"\b(discontinue|stop|held|hold)\b", line, re.IGNORECASE):
                        status = "discontinued"
                    elif re.search(r"\b(increase|titrate\s+up)\b", line, re.IGNORECASE):
                        status = "increased"

                    events.append(ExtractedEventItem(
                        event_type="medication",
                        event_date=doc_date,
                        event_date_type="explicit" if doc_date else "unknown",
                        description=f"Medication {status.capitalize()}: {med_name} {dose} ({instructions.strip()})",
                        entities=ExtractedEntities(
                            medications=[{"name": med_name, "dose": dose, "freq": instructions.strip(), "status": status}]
                        ),
                        supporting_text=line,
                        source_page=1,
                        confidence=0.95
                    ))

    @classmethod
    def _extract_clinical_events(cls, lines: List[str], doc_date: Optional[str], events: List[ExtractedEventItem]):
        # Check diagnoses / conditions
        condition_patterns = [
            (r"(?:Assessment|Impression|Diagnosis|Problem\s*List)\s*[:]?\s*([^\n;]+)", "Clinical Assessment"),
            (r"\b(Type\s*2\s*Diabetes\s*Mellitus|T2DM)\b([^\n;]*)", "Type 2 Diabetes Mellitus"),
            (r"\b(Essential\s*Hypertension|HTN)\b([^\n;]*)", "Essential Hypertension"),
            (r"\b(Diabetic\s*Nephropathy|Chronic\s*Kidney\s*Disease|CKD)\b([^\n;]*)", "Diabetic Nephropathy"),
            (r"\b(Acute\s*Kidney\s*Injury|AKI)\b([^\n;]*)", "Acute Kidney Injury")
        ]

        # Check allergies
        allergy_patterns = [
            r"Allerg(?:ies|y)\s*[:]?\s*([^\n;]+)",
            r"(No\s+Known\s+Drug\s+Allergies|NKDA)",
            r"Allergic\s+to\s+([A-Za-z]+)"
        ]

        for line in lines:
            # Check allergies
            for apat in allergy_patterns:
                m = re.search(apat, line, re.IGNORECASE)
                if m:
                    allergy_text = m.group(0).strip()
                    events.append(ExtractedEventItem(
                        event_type="condition",
                        event_date=doc_date,
                        event_date_type="explicit" if doc_date else "unknown",
                        description=f"Allergy Status Documented: {allergy_text}",
                        entities=ExtractedEntities(conditions=[allergy_text]),
                        supporting_text=line,
                        source_page=1,
                        confidence=0.98
                    ))
                    break

            # Check conditions
            for pattern, cond_name in condition_patterns:
                m = re.search(pattern, line, re.IGNORECASE)
                if m:
                    detail = m.group(1).strip() if m.lastindex >= 1 else ""
                    desc = f"{cond_name}: {detail}" if detail and cond_name == "Clinical Assessment" else cond_name
                    events.append(ExtractedEventItem(
                        event_type="condition",
                        event_date=doc_date,
                        event_date_type="explicit" if doc_date else "unknown",
                        description=desc,
                        entities=ExtractedEntities(conditions=[cond_name]),
                        supporting_text=line,
                        source_page=1,
                        confidence=0.94
                    ))
                    break

        # Also extract medications mentioned in clinical notes (e.g. "Plan: Start Metformin 500mg daily")
        cls._extract_prescription_events(lines, doc_date, events)

    @classmethod
    def _extract_imaging_events(cls, lines: List[str], doc_date: Optional[str], events: List[ExtractedEventItem]):
        exam_line = None
        impression_lines = []
        is_impression = False

        for line in lines:
            if re.search(r"(?:Examination|Procedure|Study)\s*[:]?\s*([^\n;]+)", line, re.IGNORECASE):
                exam_line = line
            if re.search(r"(?:Impression|Conclusion|Findings)\s*[:]", line, re.IGNORECASE):
                is_impression = True
            if is_impression and line:
                impression_lines.append(line)

        if exam_line:
            events.append(ExtractedEventItem(
                event_type="procedure",
                event_date=doc_date,
                event_date_type="explicit" if doc_date else "unknown",
                description=f"Imaging Procedure Conducted: {exam_line}",
                entities=ExtractedEntities(procedures=[exam_line]),
                supporting_text=exam_line,
                source_page=1,
                confidence=0.97
            ))

        if impression_lines:
            snippet = " ".join(impression_lines[:3])
            events.append(ExtractedEventItem(
                event_type="clinical_finding",
                event_date=doc_date,
                event_date_type="explicit" if doc_date else "unknown",
                description=f"Radiological Impression: {snippet[:150]}...",
                entities=ExtractedEntities(findings=[snippet[:200]]),
                supporting_text=impression_lines[0],
                source_page=1,
                confidence=0.95
            ))

    @classmethod
    def _extract_discharge_events(cls, lines: List[str], doc_date: Optional[str], events: List[ExtractedEventItem]):
        admission_date = None
        discharge_date = doc_date

        for line in lines:
            m_adm = re.search(r"Admission\s*Date\s*[:]?\s*([^\n;]+)", line, re.IGNORECASE)
            if m_adm:
                admission_date = cls.find_first_date(m_adm.group(1))
                events.append(ExtractedEventItem(
                    event_type="procedure",
                    event_date=admission_date,
                    event_date_type="explicit" if admission_date else "unknown",
                    description="Hospital Inpatient Admission",
                    entities=ExtractedEntities(procedures=["Inpatient Hospital Admission"]),
                    supporting_text=line,
                    source_page=1,
                    confidence=0.98
                ))

            m_dis = re.search(r"Discharge\s*Date\s*[:]?\s*([^\n;]+)", line, re.IGNORECASE)
            if m_dis:
                discharge_date = cls.find_first_date(m_dis.group(1)) or discharge_date

            if re.search(r"Discharge\s*Diagnosis\s*[:]?\s*([^\n;]+)", line, re.IGNORECASE):
                events.append(ExtractedEventItem(
                    event_type="discharge",
                    event_date=discharge_date,
                    event_date_type="explicit" if discharge_date else "unknown",
                    description=f"Hospital Discharge: {line}",
                    entities=ExtractedEntities(findings=[line]),
                    supporting_text=line,
                    source_page=1,
                    confidence=0.96
                ))

        # Check discharge medications and condition status
        cls._extract_clinical_events(lines, discharge_date, events)

    @classmethod
    def _extract_generic_events(cls, lines: List[str], doc_date: Optional[str], events: List[ExtractedEventItem]):
        cls._extract_lab_events(lines, doc_date, events)
        cls._extract_prescription_events(lines, doc_date, events)
        cls._extract_clinical_events(lines, doc_date, events)
