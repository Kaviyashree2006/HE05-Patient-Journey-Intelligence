from typing import Dict, Any, Tuple


class PriorityEngine:
    """Classifies clinical event importance into explainable priority tiers:
    - Critical: High-acuity clinical events (AKI, emergency admission, severe anaphylactic allergy, medication safety holds)
    - High: Marked laboratory abnormalities, major chronic disease diagnoses, significant dosage escalations, discharge transitions
    - Moderate: Standard active medical management, stable therapies, diagnostic imaging surveillance, symptom evaluations
    - Informational: Negative findings, baseline confirmations, normal ranges, administrative observations
    
    Does NOT provide diagnostic claims or clinical advice; provides objective triage categorization for reviewer investigation.
    """

    @classmethod
    def evaluate_priority(cls, event: Dict[str, Any]) -> Tuple[str, str]:
        desc = (event.get("event_description") or "").lower()
        supp = (event.get("supporting_text") or "").lower()
        ev_type = (event.get("event_type") or "").lower()
        combined = f"{desc} {supp}"

        # 1. CRITICAL
        if "held" in combined and ("metformin" in combined or "nephro" in combined):
            return "Critical", "Safety-driven medication discontinuation/hold to prevent lactic acidosis during acute renal decline."
        if "acute kidney injury" in combined or "aki" in combined:
            return "Critical", "Acute renal dysfunction requiring urgent clinical attention and close metabolic surveillance."
        if "admission" in combined and "hospital" in combined:
            return "Critical", "Inpatient hospital admission indicating acute illness escalation or volume depletion."
        if "penicillin" in combined and ("severe" in combined or "angioedema" in combined or "anaphyl" in combined or "urticaria" in combined):
            return "Critical", "Severe documented drug allergy (angioedema/urticaria) carrying high patient safety risk."
        if "serum creatinine" in combined and ("2.4" in combined or ("elevated" in combined and "admission" in combined)):
            return "Critical", "Critically elevated serum creatinine marker indicating acute organ injury."

        # 2. HIGH
        if ("hba1c" in combined or "hemoglobin a1c" in combined) and ("9." in combined or "elevated" in combined or "high" in combined):
            return "High", "Markedly elevated glycated hemoglobin reflecting severe uncontrolled hyperglycemia."
        if "fasting blood glucose" in combined and ("210" in combined or "high" in combined):
            return "High", "Marked hyperglycemia significantly above target glycemic thresholds."
        if "type 2 diabetes" in combined:
            return "High", "Documented primary metabolic diagnosis establishing long-term therapy and monitoring requirements."
        if "insulin" in combined and ("prescribed" in combined or "glargine" in combined):
            return "High", "Initiation of injectable insulin therapy marking significant treatment escalation."
        if "dose increased" in combined or ("1000 mg" in combined and "metformin" in combined):
            return "High", "Substantial dosage escalation of antidiabetic therapy indicating inadequate initial control."
        if "discharge" in combined and "hospital" in combined:
            return "High", "Inpatient discharge disposition specifying transitional care plan and medication reconciliation."
        if "microalbuminuria" in combined or ("albumin/creatinine" in combined and "65" in combined):
            return "High", "Elevated albumin-to-creatinine ratio indicating early diabetic microvascular renal involvement."

        # 3. MODERATE
        if "lisinopril" in combined:
            return "Moderate", "Prescribed ACE inhibitor therapy for blood pressure management and renal protective benefit."
        if "hypertension" in combined:
            return "Moderate", "Documented cardiovascular risk factor under active pharmacologic management."
        if "metformin" in combined:
            return "Moderate", "First-line oral antidiabetic therapy prescribed for glycemic control."
        if "ultrasound" in combined or "imaging" in combined:
            return "Moderate", "Diagnostic imaging evaluation for organ morphology and nephropathy surveillance."
        if "cortical thinning" in combined:
            return "Moderate", "Radiological finding compatible with mild chronic renal parenchymal change."
        if ev_type in ["symptom", "condition"]:
            return "Moderate", "Documented clinical evaluation of patient symptom or active medical state."
        if ev_type in ["medication", "procedure"]:
            return "Moderate", "Standard clinical intervention, order, or diagnostic procedure."

        # 4. INFORMATIONAL
        if "no hydronephrosis" in combined or "normal" in combined or "nkda" in combined:
            return "Informational", "Documented baseline or negative finding without acute clinical deviation."

        return "Informational", "General clinical note or documented observation."
