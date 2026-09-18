from typing import List, Dict, Any, Optional
from datetime import datetime


class TemporalEngine:
    """Manages temporal reasoning, event chronology, date normalization, and date certainty."""

    @staticmethod
    def parse_sort_key(date_str: Optional[str]) -> str:
        """Returns ISO string 'YYYY-MM-DD' or a future fallback key for events without dates."""
        if not date_str:
            return "9999-99-99"
        cleaned = date_str.strip()
        # If it's already YYYY-MM-DD
        if len(cleaned) == 10 and cleaned[4] == "-" and cleaned[7] == "-":
            return cleaned
        try:
            dt = datetime.fromisoformat(cleaned)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return cleaned

    @classmethod
    def sort_events_chronologically(cls, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sorts medical events chronologically by actual event date."""
        return sorted(events, key=lambda ev: (cls.parse_sort_key(ev.get("event_date")), ev.get("created_at") or ""))

    @classmethod
    def calculate_date_range(cls, events: List[Dict[str, Any]]) -> Dict[str, Optional[str]]:
        """Finds earliest and latest explicit/relative event dates in the timeline."""
        valid_dates = [
            ev["event_date"] for ev in events
            if ev.get("event_date") and ev.get("event_date_type") in ["explicit", "relative"]
        ]
        if not valid_dates:
            return {"start_date": None, "end_date": None, "total_span_days": 0}

        sorted_dates = sorted(valid_dates, key=cls.parse_sort_key)
        earliest = sorted_dates[0]
        latest = sorted_dates[-1]

        days = 0
        try:
            d1 = datetime.strptime(earliest, "%Y-%m-%d")
            d2 = datetime.strptime(latest, "%Y-%m-%d")
            days = abs((d2 - d1).days)
        except Exception:
            pass

        return {
            "start_date": earliest,
            "end_date": latest,
            "total_span_days": days
        }
