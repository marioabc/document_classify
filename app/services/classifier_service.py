import re
import logging
from typing import List, Tuple
from app.models import DocumentType

logger = logging.getLogger(__name__)


class DocumentClassifier:
    def __init__(self):
        # Import LLM classifier (lazy import to avoid circular dependencies)
        try:
            from app.services.llm_classifier_service import llm_classifier_service
            self.llm_classifier = llm_classifier_service
        except Exception as e:
            logger.warning(f"Failed to import LLM classifier: {e}")
            self.llm_classifier = None

        # Define classification rules (fallback)
        self.classification_rules = {
            DocumentType.GRUPA_KRWI: [
                'grupa krwi', 'rh', 'blood group', 'a+', 'a-', 'b+', 'b-', 'ab+', 'ab-', 'o+', 'o-'
            ],
            DocumentType.MORFOLOGIA: [
                'morfologia', 'wbc', 'rbc', 'hemoglobina', 'leukocyty', 'erytrocyty', 'hgb', 'hematokryt'
            ],
            DocumentType.APTT: [
                'aptt', 'czas częściowej tromboplastyny', 'activated partial thromboplastin'
            ],
            DocumentType.PT_INR: [
                'pt', 'inr', 'czas protrombinowy', 'prothrombin time'
            ],
            DocumentType.INR_ANTYKOAGULANTY: [
                'inr', 'antykoagulanty', 'antykoagulant', 'warfaryna', 'acenokumarol'
            ],
            DocumentType.SZCZEPIENIE_WZW: [
                'szczepienie', 'wzw', 'wirus zapalenia wątroby', 'hepatitis b', 'szczepionka'
            ],
            DocumentType.POZIOM_HBS: [
                'przeciwciał', 'hbs', 'anti-hbs', 'poziom przeciwciał'
            ],
            DocumentType.ANTYGEN_HBS: [
                'antygen', 'hbs', 'hbsag'
            ],
            DocumentType.ANTYGEN_HCV: [
                'antygen', 'hcv', 'anti-hcv', 'wirus zapalenia wątroby typu c'
            ],
            DocumentType.KARTA_INFORMACYJNA: [
                'karta informacyjna', 'pobyt', 'szpital', 'oddział', 'rozpoznanie'
            ],
            DocumentType.OPIS_ZABIEGU: [
                'zabieg', 'operacja', 'operacyjny', 'chirurg', 'procedura'
            ],
            DocumentType.JONOGRAM: [
                'jonogram', 'sód', 'potas', 'elektrolity', 'na+', 'k+', 'chlorki'
            ],
            DocumentType.GLUKOZA: [
                'glukoza', 'cukier', 'na czczo', 'glucose'
            ],
            DocumentType.KREATYNINA_MOCZNIK: [
                'kreatynina', 'mocznik', 'creatinine', 'urea'
            ],
            DocumentType.TSH_FT3_FT4: [
                'tsh', 'ft3', 'ft4', 'tarczyca', 'hormon', 'tyrotropina'
            ],
            DocumentType.RTG_KLATKA: [
                'rtg', 'rentgen', 'klatka piersiowa', 'chest x-ray', 'radiogram'
            ],
            DocumentType.EKG: [
                'ekg', 'elektrokardiogram', 'ecg', 'serce', 'rytm'
            ],
            DocumentType.ZASWIADCZENIE_INTERNISTA: [
                'zaświadczenie', 'internista', 'medycyna wewnętrzna', 'pediatra'
            ],
            DocumentType.ZASWIADCZENIE_KARDIOLOG: [
                'zaświadczenie', 'kardiolog', 'kardiologia', 'serce'
            ],
            DocumentType.ZASWIADCZENIE_NEUROLOG: [
                'zaświadczenie', 'neurolog', 'neurologia', 'neurologiczny'
            ],
            DocumentType.ZASWIADCZENIE_ENDOKRYNOLOG: [
                'zaświadczenie', 'endokrynolog', 'diabetolog', 'cukrzyca', 'endokrynologia'
            ],
            DocumentType.ZASWIADCZENIE_ONKOLOG: [
                'zaświadczenie', 'onkolog', 'onkologia', 'nowotwór'
            ],
        }

    def classify(self, text: str) -> Tuple[DocumentType, float, List[str]]:
        """
        Classify document based on extracted text using LLM-first approach
        Returns: (document_type, confidence, keywords_found)
        """
        # Try LLM classification first (primary method)
        if self.llm_classifier and self.llm_classifier.enabled:
            llm_type, llm_confidence, llm_reasoning = self.llm_classifier.classify(text)

            if llm_type and llm_confidence > 0.0:
                logger.info(f"✓ LLM Classification: {llm_type} (confidence: {llm_confidence:.2f})")
                logger.debug(f"  Reasoning: {llm_reasoning}")

                # Extract keywords for reference (but don't use for validation)
                keywords_for_type = self.classification_rules.get(llm_type, [])
                found_keywords = [kw for kw in keywords_for_type if kw.lower() in text.lower()]

                # Trust LLM decision - return its classification
                return llm_type, llm_confidence, found_keywords if found_keywords else [llm_reasoning]
            else:
                logger.warning(f"LLM returned no classification or zero confidence")

        # Fallback to rule-based classification only if LLM is disabled or failed
        logger.info("⚠ Falling back to rule-based classification (LLM unavailable)")
        rule_type, rule_confidence, rule_keywords = self._classify_rules_based(text)
        return rule_type, rule_confidence, rule_keywords

    def _classify_rules_based(self, text: str) -> Tuple[DocumentType, float, List[str]]:
        """
        Rule-based classification (original method)
        Returns: (document_type, confidence, keywords_found)
        """
        text_lower = text.lower()

        best_match = DocumentType.INNE
        best_score = 0.0
        best_keywords = []

        for doc_type, keywords in self.classification_rules.items():
            found_keywords = []
            score = 0

            for keyword in keywords:
                if keyword.lower() in text_lower:
                    found_keywords.append(keyword)
                    score += 1

            # Calculate confidence based on number of matching keywords
            if score > 0:
                confidence = min(score / len(keywords), 1.0)

                if confidence > best_score:
                    best_score = confidence
                    best_match = doc_type
                    best_keywords = found_keywords

        # Boost confidence for exact matches
        if best_score > 0:
            best_score = min(best_score * 1.2, 1.0)

        logger.info(f"Rule-based classification: {best_match} (confidence: {best_score:.2f})")

        return best_match, best_score, best_keywords

    def extract_dates(self, text: str) -> List[str]:
        """
        Extract dates from text in Polish formats
        """
        date_patterns = [
            r'\d{2}[-./]\d{2}[-./]\d{4}',  # DD-MM-YYYY
            r'\d{4}[-./]\d{2}[-./]\d{2}',  # YYYY-MM-DD
            r'\d{2}\s+(?:stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|sierpnia|września|października|listopada|grudnia)\s+\d{4}',  # DD month YYYY
        ]

        dates = []
        for pattern in date_patterns:
            found = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(found)

        return list(set(dates))  # Remove duplicates


# Singleton instance
classifier_service = DocumentClassifier()
