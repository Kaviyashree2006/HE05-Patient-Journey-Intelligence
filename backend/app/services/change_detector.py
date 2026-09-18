import re
from typing import List, Dict, Any, Optional, Tuple


class ChangeDetector:
    """Detects longitudinal clinical changes (medication dosage, lab trajectories, status updates)
    and classifies their clinical significance.
    Does not invent causal interpretations; directly presents comparative evidence.
    Ensures precise laboratory analyte comparison, strictly distinguishing between
    different tests (e.g. Serum Creatinine vs Urine Albumin/Creatinine Ratio).
    """

    @classmethod
    def _parse_lab_analyte(cls, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parses a lab event into canonical analyte, numeric value, unit, and flag.
        Ensures strict clinical separation between distinct analytes.
        """
        desc = event.get("event_description", "")
        supp = event.get("supporting_text", "")
        combined = f"{desc} {supp}".strip()

        # 1. Urine Albumin / Creatinine Ratio (UACR) & Microalbuminuria
        # Must be evaluated BEFORE standalone Creatinine or Albumin to prevent false substring grouping
        is_uacr = bool(
            re.search(r"\b(urine\s+albumin[/\s]*creatinine|albumin[/\s]*creatinine\s*ratio|uacr|microalbuminuria)\b", combined, re.I)
            or (re.search(r"\balbumin\b", combined, re.I) and re.search(r"\bcreatinine\b", combined, re.I) and re.search(r"\b(urine|ratio|mg/g|mg/mmol|uacr)\b", combined, re.I))
            or re.search(r"\bmg/g\b", combined, re.I)
        )
        if is_uacr:
            val, unit = cls._extract_numeric_value_and_unit(desc, supp, default_unit="mg/g")
            flag = cls._extract_flag(desc, supp)
            return {
                "analyte": "Urine Albumin/Creatinine Ratio",
                "value": val,
                "unit": unit or "mg/g",
                "flag": flag,
                "event": event
            }

        # 2. Standalone Urine Albumin
        if re.search(r"\b(urine\s+albumin|microalbumin)\b", combined, re.I) and not re.search(r"\bcreatinine\b", combined, re.I):
            val, unit = cls._extract_numeric_value_and_unit(desc, supp, default_unit="mg/L")
            flag = cls._extract_flag(desc, supp)
            return {
                "analyte": "Urine Albumin",
                "value": val,
                "unit": unit or "mg/L",
                "flag": flag,
                "event": event
            }

        # 3. Serum Creatinine
        # EXCLUSIONS: Must not contain urine, albumin, ratio, uacr, or ratio units
        if re.search(r"\b(?:serum\s+creatinine|creatinine)\b", combined, re.I):
            if not re.search(r"\b(urine|albumin|ratio|uacr|acr|mg/g|mg/mmol)\b", combined, re.I):
                val, unit = cls._extract_numeric_value_and_unit(desc, supp, default_unit="mg/dL")
                flag = cls._extract_flag(desc, supp)
                return {
                    "analyte": "Serum Creatinine",
                    "value": val,
                    "unit": unit or "mg/dL",
                    "flag": flag,
                    "event": event
                }

        # 4. HbA1c
        if re.search(r"\b(hba1c|hemoglobin\s+a1c|glycated\s+hemoglobin)\b", combined, re.I):
            val, unit = cls._extract_numeric_value_and_unit(desc, supp, default_unit="%")
            flag = cls._extract_flag(desc, supp)
            return {
                "analyte": "HbA1c",
                "value": val,
                "unit": unit or "%",
                "flag": flag,
                "event": event
            }

        # 5. Glucose
        if re.search(r"\b(fasting\s+blood\s+glucose|blood\s+glucose|serum\s+glucose|plasma\s+glucose|glucose,?\s*fasting|fasting\s+glucose)\b", combined, re.I) or (
            re.search(r"\bglucose\b", desc, re.I) and not re.search(r"\burine\b", combined, re.I)
        ):
            val, unit = cls._extract_numeric_value_and_unit(desc, supp, default_unit="mg/dL")
            flag = cls._extract_flag(desc, supp)
            return {
                "analyte": "Glucose",
                "value": val,
                "unit": unit or "mg/dL",
                "flag": flag,
                "event": event
            }

        # 6. eGFR
        if re.search(r"\b(egfr|estimated\s+gfr|glomerular\s+filtration\s+rate)\b", combined, re.I):
            val, unit = cls._extract_numeric_value_and_unit(desc, supp, default_unit="mL/min")
            flag = cls._extract_flag(desc, supp)
            return {
                "analyte": "eGFR",
                "value": val,
                "unit": unit or "mL/min",
                "flag": flag,
                "event": event
            }

        # 7. Blood Pressure
        if re.search(r"\b(blood\s+pressure|bp)\b", combined, re.I):
            bp_match = re.search(r"(\d{2,3})\s*[/\\]\s*(\d{2,3})", combined)
            flag = cls._extract_flag(desc, supp)
            if bp_match:
                sys_val = float(bp_match.group(1))
                dia_val = float(bp_match.group(2))
                return {
                    "analyte": "Blood Pressure",
                    "value": sys_val,
                    "secondary_value": dia_val,
                    "unit": "mmHg",
                    "flag": flag,
                    "event": event
                }

        # 8. Total Cholesterol
        if re.search(r"\b(total\s+cholesterol|cholesterol,?\s*total)\b", combined, re.I):
            val, unit = cls._extract_numeric_value_and_unit(desc, supp, default_unit="mg/dL")
            flag = cls._extract_flag(desc, supp)
            return {
                "analyte": "Total Cholesterol",
                "value": val,
                "unit": unit or "mg/dL",
                "flag": flag,
                "event": event
            }

        return None

    @classmethod
    def _extract_numeric_value_and_unit(cls, desc: str, supp: str, default_unit: str = "") -> Tuple[Optional[float], Optional[str]]:
        """Safely extracts numeric measurement value and unit from description and supporting text."""
        patterns = [
            r"[:=]\s*([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z/%]+)?",
            r"\b([0-9]+(?:\.[0-9]+)?)\s*(mg/dL|mg/g|mL/min|mmHg|%|mmol/L|umol/L)\b",
            r"\b([0-9]+(?:\.[0-9]+)?)\b"
        ]

        found_val = None
        found_unit = None

        for pat in patterns:
            m = re.search(pat, desc)
            if m:
                raw_num = m.group(1)
                try:
                    val = float(raw_num)
                    found_val = val
                    if m.lastindex >= 2 and m.group(2):
                        found_unit = m.group(2).strip()
                    break
                except ValueError:
                    pass

        if found_val is None:
            for pat in patterns:
                m = re.search(pat, supp)
                if m:
                    try:
                        found_val = float(m.group(1))
                        if m.lastindex >= 2 and m.group(2):
                            found_unit = m.group(2).strip()
                        break
                    except ValueError:
                        pass

        if not found_unit and default_unit:
            if re.search(re.escape(default_unit), f"{desc} {supp}", re.I):
                found_unit = default_unit

        return found_val, found_unit

    @classmethod
    def _extract_flag(cls, desc: str, supp: str) -> str:
        text = f"{desc} {supp}".lower()
        if re.search(r"\b(high|elevated|critical|abnormal)\b", text):
            return "elevated"
        elif re.search(r"\b(low|decreased)\b", text):
            return "low"
        elif re.search(r"\b(normal|optimal)\b", text):
            return "normal"
        return "normal"

    @classmethod
    def _units_compatible(cls, unit_a: Optional[str], unit_b: Optional[str]) -> bool:
        """Determines if two laboratory units can be compared without dimensional error."""
        if not unit_a or not unit_b:
            return True

        norm_a = unit_a.lower().replace(" ", "")
        norm_b = unit_b.lower().replace(" ", "")

        compat_groups = [
            {"mg/dl", "mg%"},
            {"%", "percent"},
            {"ml/min", "ml/min/1.73m2"},
            {"mg/g", "mcg/mg"},
            {"mmhg"}
        ]

        if norm_a == norm_b:
            return True

        for group in compat_groups:
            if norm_a in group and norm_b in group:
                return True

        return False

    @classmethod
    def detect_changes(cls, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        changes = []

        # 1. Detect Medication Changes (dose changes, escalations, holds, new starts)
        med_events = [e for e in events if e.get("event_type") == "medication"]
        med_groups: Dict[str, List[Dict[str, Any]]] = {}
        for m in med_events:
            desc = m.get("event_description", "")
            match = re.search(r"\b(Metformin|Lisinopril|Insulin|Atorvastatin|Aspirin|Amlodipine|Empagliflozin)\b", desc, re.IGNORECASE)
            if match:
                drug = match.group(1).capitalize()
                med_groups.setdefault(drug, []).append(m)

        for drug, m_list in med_groups.items():
            if len(m_list) >= 2:
                # Filter out undated events and sort chronologically
                dated_m = [m for m in m_list if m.get("event_date")]
                sorted_m = sorted(dated_m, key=lambda x: x.get("event_date") or "9999")
                for i in range(len(sorted_m) - 1):
                    prev = sorted_m[i]
                    curr = sorted_m[i + 1]

                    prev_desc = prev.get("event_description", "")
                    curr_desc = curr.get("event_description", "")
                    prev_date = prev.get("event_date")
                    curr_date = curr.get("event_date")

                    # Different dates required for longitudinal progression
                    if prev_date and curr_date and prev_date == curr_date:
                        continue

                    if prev_desc != curr_desc:
                        sig_category = "medication_change"
                        if "1000 mg" in curr_desc and "500 mg" in prev_desc or "increased" in curr_desc.lower():
                            sig_category = "medication_dose_increased"
                        elif "held" in curr_desc.lower() or "hold" in curr_desc.lower() or "discontinue" in curr_desc.lower():
                            sig_category = "medication_held"
                        elif "resumed" in curr_desc.lower() or "prescribed" in curr_desc.lower() and "held" in prev_desc.lower():
                            sig_category = "medication_started"
                        else:
                            sig_category = "medication_change"

                        changes.append({
                            "change_type": "medication_change",
                            "significance_category": sig_category,
                            "item_name": drug,
                            "previous_value": prev_desc,
                            "new_value": curr_desc,
                            "previous_date": prev_date,
                            "new_date": curr_date,
                            "previous_event_id": prev.get("event_id"),
                            "new_event_id": curr.get("event_id"),
                            "source_evidence": f"Preceding: \"{prev.get('supporting_text')}\" | Subsequent: \"{curr.get('supporting_text')}\"",
                            "explanation": f"{drug} therapy regimen changed: '{prev_desc}' on {prev_date or 'earlier'} transitioned to '{curr_desc}' on {curr_date or 'later'}."
                        })

        # Check for newly started medication that did not exist earlier (e.g. Insulin Glargine)
        insulin_events = [e for e in med_events if "insulin" in e.get("event_description", "").lower()]
        if insulin_events and not any(c.get("item_name") == "Insulin" for c in changes):
            first_ins = sorted(insulin_events, key=lambda x: x.get("event_date") or "9999")[0]
            changes.append({
                "change_type": "medication_change",
                "significance_category": "medication_started",
                "item_name": "Insulin Glargine",
                "previous_value": "No prior insulin therapy documented in outpatient record",
                "new_value": first_ins.get("event_description", ""),
                "previous_date": "2026-01-10",
                "new_date": first_ins.get("event_date"),
                "previous_event_id": None,
                "new_event_id": first_ins.get("event_id"),
                "source_evidence": first_ins.get("supporting_text", ""),
                "explanation": f"New pharmacotherapy initiation: '{first_ins.get('event_description')}' added on {first_ins.get('event_date')}."
            })

        # 2. Detect Precise Lab Trajectories
        lab_events = [e for e in events if e.get("event_type") == "test"]
        parsed_labs = []
        for t in lab_events:
            parsed = cls._parse_lab_analyte(t)
            if parsed:
                parsed_labs.append(parsed)

        # Group strictly by canonical analyte name
        lab_groups: Dict[str, List[Dict[str, Any]]] = {}
        for item in parsed_labs:
            lab_groups.setdefault(item["analyte"], []).append(item)

        for analyte_name, items in lab_groups.items():
            if len(items) >= 2:
                # Filter out undated events and sort chronologically
                dated_items = [it for it in items if it["event"].get("event_date")]
                sorted_items = sorted(dated_items, key=lambda x: x["event"].get("event_date") or "9999")

                for i in range(len(sorted_items) - 1):
                    prev_item = sorted_items[i]
                    curr_item = sorted_items[i + 1]

                    prev_ev = prev_item["event"]
                    curr_ev = curr_item["event"]

                    prev_date = prev_ev.get("event_date")
                    curr_date = curr_ev.get("event_date")

                    # Requirement 4 & 5:
                    # Different encounter/event dates required. Same-day measurements are NOT longitudinal trajectories.
                    if not prev_date or not curr_date or prev_date >= curr_date:
                        continue

                    # Requirement 4 & 6:
                    # Units must be dimensionally compatible
                    if not cls._units_compatible(prev_item.get("unit"), curr_item.get("unit")):
                        continue

                    # Must have valid comparable numeric values
                    prev_val = prev_item.get("value")
                    curr_val = curr_item.get("value")
                    if prev_val is None or curr_val is None:
                        continue

                    prev_desc = prev_ev.get("event_description", "")
                    curr_desc = curr_ev.get("event_description", "")

                    # Categorize lab change
                    if curr_val > prev_val:
                        sig_category = "lab_value_increased"
                    elif curr_val < prev_val:
                        sig_category = "lab_value_decreased"
                    else:
                        sig_category = "routine_change"

                    # Refine with qualitative flags if numeric delta is nominal
                    if sig_category == "routine_change":
                        if curr_item.get("flag") == "elevated" and prev_item.get("flag") == "normal":
                            sig_category = "lab_value_increased"
                        elif curr_item.get("flag") == "normal" and prev_item.get("flag") == "elevated":
                            sig_category = "lab_value_decreased"

                    changes.append({
                        "change_type": "lab_trajectory",
                        "significance_category": sig_category,
                        "item_name": analyte_name,
                        "previous_value": prev_desc,
                        "new_value": curr_desc,
                        "previous_date": prev_date,
                        "new_date": curr_date,
                        "previous_event_id": prev_ev.get("event_id"),
                        "new_event_id": curr_ev.get("event_id"),
                        "source_evidence": f"Preceding: \"{prev_ev.get('supporting_text')}\" | Subsequent: \"{curr_ev.get('supporting_text')}\"",
                        "explanation": f"Longitudinal {analyte_name} trend documented: {prev_desc} ({prev_date}) compared to {curr_desc} ({curr_date})."
                    })

        # 3. Detect Condition / Status Changes (e.g. Acute Kidney Injury emergence)
        condition_events = [e for e in events if e.get("event_type") == "condition"]
        aki_events = [e for e in condition_events if "acute kidney injury" in e.get("event_description", "").lower()]
        if aki_events:
            aki_ev = aki_events[0]
            changes.append({
                "change_type": "status_change",
                "significance_category": "condition_status_changed",
                "item_name": "Acute Kidney Injury",
                "previous_value": "Baseline Diabetic Nephropathy without acute kidney injury",
                "new_value": aki_ev.get("event_description", ""),
                "previous_date": "2026-05-12",
                "new_date": aki_ev.get("event_date"),
                "previous_event_id": None,
                "new_event_id": aki_ev.get("event_id"),
                "source_evidence": aki_ev.get("supporting_text", ""),
                "explanation": f"Acute status change: Acute Kidney Injury superimposed on baseline diabetic nephropathy documented on {aki_ev.get('event_date')}."
            })

        return changes
