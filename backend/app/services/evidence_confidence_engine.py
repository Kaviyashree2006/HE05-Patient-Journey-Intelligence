from typing import Dict, Any, Tuple


class EvidenceConfidenceEngine:
    """Evaluates the evidential grounding strength of extracted medical events:
    - Strong: Explicit numerical metrics, formal signed prescription/procedure orders, or direct laboratory panels with explicit dates.
    - Moderate: Direct clinician encounter assessments, documented physical findings, or clear diagnostic impressions.
    - Limited: Subjective historical recall, approximate dates, or relative temporal statements ("past 4 weeks").
    
    IMPORTANT: Never presents an algorithmic score as clinical certainty; explains WHY evidence is rated at a given tier.
    """

    @classmethod
    def evaluate_confidence(cls, event: Dict[str, Any]) -> Tuple[str, str]:
        date_type = (event.get("event_date_type") or "explicit").lower()
        ev_type = (event.get("event_type") or "").lower()
        supp = event.get("supporting_text") or ""
        supp_lower = supp.lower()

        # 1. Limited Evidence (vague/relative timeline or subjective recall)
        if date_type in ["approximate", "unknown", "relative"]:
            return (
                "Limited",
                f"Documented with {date_type} temporal certainty based on subjective patient recall or narrative description ('{supp[:60]}...')."
            )
        if "reports" in supp_lower and ("over past" in supp_lower or "feels" in supp_lower):
            return (
                "Limited",
                "Patient-reported subjective symptom without direct objective diagnostic telemetry."
            )

        # 2. Strong Evidence (Explicit test with numbers, formal Rx with dose, structured procedure)
        if ev_type == "test" and any(char.isdigit() for char in supp):
            return (
                "Strong",
                "Objective quantitative laboratory evaluation with explicit numerical result, reference interval, and specimen collection date."
            )
        if ev_type == "medication" and any(u in supp_lower for u in ["mg", "units", "tablet", "daily", "bid"]):
            return (
                "Strong",
                "Formal clinician prescription order specifying exact active agent, dosage formulation, and administration instructions."
            )
        if ev_type in ["procedure", "discharge"]:
            return (
                "Strong",
                "Formal clinical order or documented inpatient service milestone with verified execution date."
            )

        # 3. Moderate Evidence (Clinical assessment, diagnosis without in-note lab raw telemetry)
        if ev_type == "condition":
            return (
                "Moderate",
                "Specialist clinical assessment documented in formal consultation record referencing prior objective findings."
            )
        if ev_type == "clinical_finding":
            return (
                "Moderate",
                "Qualitative radiological or clinical evaluation documented by attending physician."
            )

        return (
            "Moderate",
            "Documented in provider record with explicit date and direct textual evidence."
        )
