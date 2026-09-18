import re
from typing import Tuple


class DocumentClassifier:
    """Classifies raw medical document text into standard document categories."""

    LAB_KEYWORDS = [
        r"\blaboratory\b", r"\blab report\b", r"\bpathology\b", r"\bpanel\b",
        r"\bhba1c\b", r"\bglucose\b", r"\bcreatinine\b", r"\begfr\b",
        r"\bhemoglobin\b", r"\bcholesterol\b", r"\breference interval\b",
        r"\breference range\b", r"\bspecimen\b", r"\bblood test\b", r"\burinalysis\b"
    ]

    PRESCRIPTION_KEYWORDS = [
        r"\bprescription\b", r"\brx\b", r"\bsig\b", r"\bdispense\b",
        r"\brefills?\b", r"\btablets?\b", r"\bcapsules?\b", r"\bmg\b",
        r"\bpo\b", r"\bqd\b", r"\bbid\b", r"\btid\b", r"\bprescribed\b",
        r"\bpharmacy\b", r"\broute:\b", r"\bdose:\b"
    ]

    CLINICAL_NOTE_KEYWORDS = [
        r"\bclinical note\b", r"\bconsultation\b", r"\bprogress note\b",
        r"\bsoap note\b", r"\bchief complaint\b", r"\bhpi\b",
        r"\bhistory of present illness\b", r"\bphysical exam\b",
        r"\bassessment and plan\b", r"\boutpatient clinic\b", r"\bconsult note\b"
    ]

    IMAGING_KEYWORDS = [
        r"\bultrasound\b", r"\bimaging report\b", r"\bx-ray\b", r"\bmri\b",
        r"\bct scan\b", r"\bradiology\b", r"\bfindings:\b", r"\bimpression:\b",
        r"\bexamination:\b", r"\bsonogram\b", r"\bechocardiogram\b", r"\btechnique:\b"
    ]

    DISCHARGE_KEYWORDS = [
        r"\bdischarge summary\b", r"\badmission date\b", r"\bdischarge date\b",
        r"\bhospital course\b", r"\bdischarge diagnosis\b", r"\bcondition on discharge\b",
        r"\bdischarge medications\b", r"\bdisposition\b", r"\binpatient summary\b"
    ]

    @classmethod
    def classify(cls, text: str, filename: str = "") -> Tuple[str, float]:
        """Returns (predicted_type, confidence)."""
        combined = f"{filename} {text}".lower()

        scores = {
            "discharge_summary": 0,
            "imaging_report": 0,
            "prescription": 0,
            "lab_report": 0,
            "clinical_note": 0,
        }

        # Filename hints have high weight
        lower_fn = filename.lower()
        if "discharge" in lower_fn:
            scores["discharge_summary"] += 6
        if "imaging" in lower_fn or "ultrasound" in lower_fn or "mri" in lower_fn or "ct" in lower_fn or "xray" in lower_fn:
            scores["imaging_report"] += 6
        if "prescription" in lower_fn or "rx" in lower_fn:
            scores["prescription"] += 6
        if "lab" in lower_fn or "blood" in lower_fn or "panel" in lower_fn:
            scores["lab_report"] += 6
        if "consult" in lower_fn or "note" in lower_fn or "clinical" in lower_fn:
            scores["clinical_note"] += 5

        # Check content keywords
        for pattern in cls.DISCHARGE_KEYWORDS:
            if re.search(pattern, combined):
                scores["discharge_summary"] += 2

        for pattern in cls.IMAGING_KEYWORDS:
            if re.search(pattern, combined):
                scores["imaging_report"] += 2

        for pattern in cls.PRESCRIPTION_KEYWORDS:
            if re.search(pattern, combined):
                scores["prescription"] += 2

        for pattern in cls.LAB_KEYWORDS:
            if re.search(pattern, combined):
                scores["lab_report"] += 2

        for pattern in cls.CLINICAL_NOTE_KEYWORDS:
            if re.search(pattern, combined):
                scores["clinical_note"] += 2

        best_type, top_score = max(scores.items(), key=lambda item: item[1])

        if top_score == 0:
            return "clinical_note", 0.5

        confidence = min(0.98, max(0.65, top_score / 12.0))
        return best_type, confidence
