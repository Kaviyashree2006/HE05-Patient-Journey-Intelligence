import os
import json
import logging
from typing import Optional
from app.schemas.models import DocumentExtractionResult

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a medical document intelligence and information extraction system.
Your job is to extract structured clinical events from the provided medical document text.

CRITICAL RULES:
1. Extract ONLY facts explicitly stated in the document. NEVER invent, hallucinate, or assume missing clinical information.
2. Distinguish the DOCUMENT DATE (when the document was created) from the EVENT DATE (when the medical event actually took place).
3. If an event date cannot be reliably determined from the text, set event_date to null and event_date_type to "unknown".
4. Assign date certainty:
   - "explicit": An exact calendar date is stated (e.g. "15 Jan 2026", "2026-01-10").
   - "relative": Stated relative to another date (e.g. "started 2 weeks ago", "3 days prior to admission").
   - "approximate": Imprecise timeframe stated (e.g. "history of diabetes for ~5 years", "several months ago").
   - "unknown": No reliable date found.
5. Every single event MUST have "supporting_text" containing the exact verbatim sentence or line from the document proving that this event happened.
6. Extract entities: conditions, symptoms, tests (name, value, unit, status), medications (name, dose, freq, status), procedures, findings.
7. Event types must be one of: condition, symptom, test, medication, procedure, clinical_finding, treatment, follow_up, discharge.
8. Output STRICT JSON conforming to the schema.
"""


class GeminiExtractor:
    """Uses Google GenAI SDK to perform structured medical event extraction."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def extract(self, text: str, filename: str, predicted_type: str) -> DocumentExtractionResult:
        if not self.is_available():
            raise ValueError("GEMINI_API_KEY is not configured.")

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.api_key)

        prompt = f"""Document filename: {filename}
Initial predicted document type: {predicted_type}

Medical Document Content:
\"\"\"
{text}
\"\"\"

Please extract the structured document metadata and all medical events according to the instructions.
Output ONLY valid JSON matching this schema:
{{
  "document_type": "lab_report | prescription | clinical_note | imaging_report | discharge_summary | other",
  "document_date": "YYYY-MM-DD or string date",
  "patient_reference": "string or null",
  "events": [
    {{
      "event_type": "condition | symptom | test | medication | procedure | clinical_finding | treatment | follow_up | discharge",
      "event_date": "YYYY-MM-DD or null",
      "event_date_type": "explicit | relative | approximate | unknown",
      "description": "Clear clinical summary",
      "entities": {{
        "conditions": ["string"],
        "symptoms": ["string"],
        "tests": [{{"name": "string", "value": "string", "unit": "string", "status": "string"}}],
        "medications": [{{"name": "string", "dose": "string", "freq": "string", "status": "string"}}],
        "procedures": ["string"],
        "findings": ["string"]
      }},
      "supporting_text": "Exact verbatim sentence from document",
      "source_page": 1,
      "confidence": 0.95
    }}
  ]
}}
"""

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.1,
                    response_mime_type="application/json",
                )
            )

            raw_json = response.text.strip()
            # Clean possible markdown wrapping if returned
            if raw_json.startswith("```"):
                raw_json = raw_json.strip("`").replace("json\n", "", 1).strip()

            parsed = json.loads(raw_json)
            return DocumentExtractionResult(**parsed)

        except Exception as e:
            logger.warning(f"Gemini API extraction failed: {e}. Falling back to clinical rule extractor.")
            raise
