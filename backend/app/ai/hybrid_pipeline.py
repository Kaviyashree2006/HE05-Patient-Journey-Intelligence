import logging
from typing import Dict, Any, List
from app.ai.gemini_extractor import GeminiExtractor
from app.ai.rule_extractor import ClinicalRuleExtractor
from app.schemas.models import DocumentExtractionResult

logger = logging.getLogger(__name__)


class HybridExtractionPipeline:
    """Orchestrates AI and clinical rule-based extraction with automated fallback."""

    def __init__(self):
        self.gemini = GeminiExtractor()

    async def extract_document(
        self,
        text: str,
        filename: str,
        predicted_type: str,
        pages: List[Dict[str, Any]] = None
    ) -> DocumentExtractionResult:
        """Extracts structured medical events from document text."""

        # 1. Try Gemini API if key is configured
        if self.gemini.is_available():
            try:
                logger.info(f"Extracting with Gemini API for: {filename}")
                result = await self.gemini.extract(text, filename, predicted_type)
                if result and result.events:
                    return result
            except Exception as e:
                logger.warning(f"Gemini API attempt failed ({e}), falling back to deterministic clinical extractor.")

        # 2. Deterministic Clinical Pattern Extractor Fallback
        logger.info(f"Extracting with Clinical Rule Extractor for: {filename}")
        rule_result = ClinicalRuleExtractor.extract(
            text=text,
            filename=filename,
            doc_type=predicted_type,
            pages=pages
        )

        # Deduplicate events with identical descriptions and dates
        unique_events = []
        seen_keys = set()
        for ev in rule_result.events:
            key = (ev.event_type, ev.event_date, ev.description.strip().lower())
            if key not in seen_keys:
                seen_keys.add(key)
                unique_events.append(ev)

        rule_result.events = unique_events
        return rule_result
