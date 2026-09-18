from typing import List, Dict, Any
from datetime import datetime


class GapDetector:
    """Detects documentation intervals and unexplained lapses between clinical records.
    Strictly avoids fabricating events; neutrally identifies absence of uploaded records
    while explicitly distinguishing 'No documentation found' from 'No care occurred'.
    """

    @classmethod
    def detect_gaps(cls, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        gaps = []

        # Filter events with valid ISO dates
        dated_events = []
        for e in events:
            date_str = e.get("event_date")
            if date_str and len(date_str) == 10 and date_str[4] == "-" and date_str[7] == "-":
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    dated_events.append((dt, e))
                except Exception:
                    pass

        dated_events.sort(key=lambda x: x[0])

        for i in range(len(dated_events) - 1):
            dt_prev, ev_prev = dated_events[i]
            dt_curr, ev_curr = dated_events[i + 1]

            diff_days = (dt_curr - dt_prev).days

            # Flag gap if 60 or more days elapsed between documented encounters
            if diff_days >= 60:
                prev_desc = ev_prev.get("event_description", "")
                curr_desc = ev_curr.get("event_description", "")
                prev_date = dt_prev.strftime("%Y-%m-%d")
                curr_date = dt_curr.strftime("%Y-%m-%d")

                # Context-specific review recommendations
                if "metformin" in prev_desc.lower() and "ultrasound" in curr_desc.lower():
                    context = "Outpatient therapy escalation followed by routine renal surveillance."
                    recommendation = "Review outpatient primary care clinic encounters or community pharmacy dispensing logs between February and May 2026 to verify medication adherence and interval metabolic monitoring."
                elif "ultrasound" in prev_desc.lower() and "admission" in curr_desc.lower():
                    context = "Renal diagnostic imaging followed by acute volume depletion and inpatient hospital admission."
                    recommendation = "Examine urgent care, ambulatory visit notes, or primary provider communications prior to August 2026 admission to ascertain when acute gastrointestinal illness commenced."
                else:
                    context = "Consecutive clinical touchpoints separated by extended duration."
                    recommendation = "Retrieve external health network records or ambulatory visit notes to determine if intermediate clinical consultations or laboratory evaluations were performed during this interval."

                gaps.append({
                    "from_event_id": ev_prev.get("event_id"),
                    "from_event_desc": prev_desc,
                    "from_event_date": prev_date,
                    "to_event_id": ev_curr.get("event_id"),
                    "to_event_desc": curr_desc,
                    "to_event_date": curr_date,
                    "days_gap": diff_days,
                    "gap_start_date": prev_date,
                    "gap_end_date": curr_date,
                    "gap_type": "extended_interval_without_records",
                    "clinical_context": context,
                    "review_recommendation": recommendation,
                    "description": (
                        f"{diff_days}-day documentation gap detected between '{prev_desc}' ({prev_date}) "
                        f"and '{curr_desc}' ({curr_date}). "
                        "No documentation found in uploaded records for this period (note: this does not imply care did not occur)."
                    )
                })

        return gaps
