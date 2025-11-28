import logging
import json
import requests
from typing import Tuple, Optional
from app.models import DocumentType
from app.config import settings

logger = logging.getLogger(__name__)


class LLMClassifierService:
    def __init__(self):
        self.enabled = False
        self.ollama_url = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434')
        self.model_name = getattr(settings, 'OLLAMA_MODEL', 'llama3.2:3b')

        # Check if Ollama is available
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            if response.status_code == 200:
                self.enabled = True
                logger.info(f"LLM Classifier initialized with Ollama model: {self.model_name}")
            else:
                logger.warning(f"Ollama server not responding correctly")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Ollama not available at {self.ollama_url}: {e}")
            logger.info("LLM Classifier disabled - install and start Ollama to enable")

    def classify(self, text: str) -> Tuple[Optional[DocumentType], float, str]:
        """
        Classify document using local LLM (Ollama)
        Returns: (document_type, confidence, reasoning)
        """
        if not self.enabled:
            logger.warning("LLM classifier is not enabled")
            return None, 0.0, "LLM classifier not enabled"

        logger.info("="*80)
        logger.info("🤖 STARTING LLM CLASSIFICATION")
        logger.info("="*80)

        try:
            # Prepare document types list for the prompt
            doc_types_list = "\n".join([
                f"- {dt.value}: {self._get_type_description(dt)}"
                for dt in DocumentType if dt != DocumentType.INNE
            ])

            logger.info(f"📄 Extracted text (first 200 chars):\n{text[:200]}...")
            logger.info(f"📊 Text length: {len(text)} characters")

            prompt = f"""Jesteś ekspertem w klasyfikacji polskich dokumentów medycznych.

Dostałeś tekst wyekstraktowany z dokumentu medycznego za pomocą OCR. Tekst może zawierać błędy OCR.

TYPY DOKUMENTÓW:
{doc_types_list}
- inne: dokumenty, które nie pasują do żadnej z powyższych kategorii

TEKST DOKUMENTU:
{text}

ZASADY KLASYFIKACJI (sprawdzaj w tej kolejności):
1. Szukaj kluczowych fraz i terminów specyficznych dla danego typu dokumentu
2. Zwracaj TYLKO typy z listy powyżej - NIGDY nie wymyślaj nowych typów
3. NAJPIERW sprawdź czy to szczepienie - TO MA PRIORYTET:
   - "szczepienie", "WZW", "wirusowe zapalenie wątroby", "hepatitis B", "typ B", "HBV" -> DOC_BADANIE_WZWB
   - Nawet jeśli jest tam słowo "zaświadczenie", jeśli chodzi o szczepienie WZW -> DOC_BADANIE_WZWB
4. Jeśli dokument to zaświadczenie (NIE o szczepieniu), sprawdź specjalizację lekarza:
   - "kardiolog", "kardiologia" -> DOC_BADANIE_LK
   - "neurolog", "neurologia" -> DOC_BADANIE_LN
   - "endokrynolog", "diabetolog" -> DOC_BADANIE_ZASEND
   - "onkolog", "onkologia" -> DOC_BADANIE_ZASONK
   - "internista", "pediatra", "ogólny" -> DOC_BADANIE_INTERN
5. Dla badań laboratoryjnych sprawdź konkretne parametry:
   - "APTT", "czas częściowej tromboplastyny" -> DOC_BADANIE_APTT
   - "PT", "INR", "czas protrombinowy" -> DOC_BADANIE_PTINR lub DOC_BADANIE_INR
   - "grupa krwi", "Rh" -> DOC_BADANIE_RH
   - "morfologia", "WBC", "RBC", "hemoglobina" -> DOC_BADANIE_MORF
6. Jeśli tekst jest pusty lub bardzo krótki (<20 znaków), zwróć "inne" z niską pewnością

PRZYKŁADY:
- "ZAŚWIADCZENIE O SZCZEPIENIU PRZECIW WZW TYPU B" -> DOC_BADANIE_WZWB (NIE DOC_BADANIE_INTERN!)
- "Zaświadczenie o szczepieniu WZW" -> DOC_BADANIE_WZWB
- "APTT 14.5" -> DOC_BADANIE_APTT (nie DOC_BADANIE_RH!)
- "Zaświadczenie, Poradnia kardiologu" -> DOC_BADANIE_LK
- "Zaświadczenie neurologiczne" -> DOC_BADANIE_LN
- "Grupa krwi 0 Rh+" -> DOC_BADANIE_RH

Przeanalizuj dokument i określ jego typ. Zwróć odpowiedź w formacie JSON:
{{
  "document_type": "typ_dokumentu",
  "confidence": 0.95,
  "reasoning": "krótkie wyjaśnienie dlaczego wybrałeś ten typ"
}}

Gdzie:
- document_type to DOKŁADNIE jedna z wartości z listy typów (np. "DOC_BADANIE_WZWB", "DOC_BADANIE_RH", "DOC_BADANIE_LK", itp.)
- confidence to wartość od 0.0 do 1.0 oznaczająca pewność klasyfikacji
- reasoning to krótkie (1-2 zdania) wyjaśnienie

WAŻNE: Zwróć TYLKO JSON, bez żadnego dodatkowego tekstu."""

            logger.info("="*80)
            logger.info("📤 FULL PROMPT SENT TO OLLAMA:")
            logger.info("="*80)
            logger.info(prompt)
            logger.info("="*80)

            # Call Ollama API
            logger.info(f"🔗 Calling Ollama API at {self.ollama_url}/api/generate")
            logger.info(f"🤖 Model: {self.model_name}")

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 500
                    }
                },
                timeout=600  # Increased to 120s for llama3.1 8B on CPU
            )

            if response.status_code != 200:
                logger.error(f"❌ Ollama API error: {response.status_code}")
                logger.error(f"Response body: {response.text[:500]}")
                return None, 0.0, f"Ollama API error: {response.status_code}"

            response_data = response.json()
            logger.info("="*80)
            logger.info("📥 FULL RESPONSE FROM OLLAMA:")
            logger.info("="*80)
            logger.info(f"Response data: {response_data}")
            logger.info("="*80)

            response_text = response_data.get("response", "").strip()
            logger.info(f"📝 Extracted response text:\n{response_text}")

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("\n", 1)[1]
                response_text = response_text.rsplit("```", 1)[0].strip()

            result = json.loads(response_text)
            logger.info(f"✅ Parsed JSON result: {result}")

            # Parse document type
            doc_type_str = result.get("document_type", "inne")
            try:
                document_type = DocumentType(doc_type_str)
                logger.info(f"✅ Document type parsed: {document_type}")
            except ValueError:
                logger.warning(f"⚠️ Unknown document type from LLM: {doc_type_str}, defaulting to INNE")
                document_type = DocumentType.INNE

            confidence = float(result.get("confidence", 0.0))
            reasoning = result.get("reasoning", "")

            logger.info("="*80)
            logger.info("✅ FINAL LLM CLASSIFICATION RESULT:")
            logger.info(f"   Document Type: {document_type}")
            logger.info(f"   Confidence: {confidence:.2f}")
            logger.info(f"   Reasoning: {reasoning}")
            logger.info("="*80)

            return document_type, confidence, reasoning

        except json.JSONDecodeError as e:
            logger.error("="*80)
            logger.error(f"❌ Failed to parse LLM response as JSON: {e}")
            logger.error(f"LLM raw response: {response_text if 'response_text' in locals() else 'N/A'}")
            logger.error("="*80)
            return None, 0.0, f"JSON parsing error: {str(e)}"
        except requests.exceptions.RequestException as e:
            logger.error("="*80)
            logger.error(f"❌ Error calling Ollama API: {str(e)}")
            logger.error("="*80)
            return None, 0.0, f"Ollama API error: {str(e)}"
        except Exception as e:
            logger.error("="*80)
            logger.error(f"❌ Error during LLM classification: {str(e)}")
            logger.error("="*80)
            return None, 0.0, f"Error: {str(e)}"

    def _get_type_description(self, doc_type: DocumentType) -> str:
        """Get human-readable description for document type"""
        descriptions = {
            DocumentType.GRUPA_KRWI: "Oznaczenie grupy krwi i czynnika Rh",
            DocumentType.MORFOLOGIA: "Morfologia krwi (WBC, RBC, hemoglobina, hematokryt)",
            DocumentType.APTT: "Badanie czasu częściowej tromboplastyny po aktywacji",
            DocumentType.PT_INR: "Czas protrombinowy i INR",
            DocumentType.INR_ANTYKOAGULANTY: "INR w kontekście leczenia antykoagulantami",
            DocumentType.SZCZEPIENIE_WZW: "Zaświadczenie o szczepieniu przeciw wirusowemu zapaleniu wątroby typu B",
            DocumentType.POZIOM_HBS: "Poziom przeciwciał anty-HBs",
            DocumentType.ANTYGEN_HBS: "Badanie antygenu HBsAg",
            DocumentType.ANTYGEN_HCV: "Badanie antygenu/przeciwciał HCV",
            DocumentType.KARTA_INFORMACYJNA: "Karta informacyjna leczenia szpitalnego",
            DocumentType.OPIS_ZABIEGU: "Opis wykonanego zabiegu operacyjnego",
            DocumentType.JONOGRAM: "Badanie elektrolitów (sód, potas, chlorki)",
            DocumentType.GLUKOZA: "Badanie poziomu glukozy",
            DocumentType.KREATYNINA_MOCZNIK: "Badanie kreatyniny i mocznika",
            DocumentType.TSH_FT3_FT4: "Badanie hormonów tarczycy",
            DocumentType.RTG_KLATKA: "Zdjęcie rentgenowskie klatki piersiowej",
            DocumentType.EKG: "Elektrokardiogram - badanie czynności serca",
            DocumentType.ZASWIADCZENIE_INTERNISTA: "Zaświadczenie od lekarza internisty lub pediatry (ogólne)",
            DocumentType.ZASWIADCZENIE_KARDIOLOG: "Zaświadczenie od kardiologa",
            DocumentType.ZASWIADCZENIE_NEUROLOG: "Zaświadczenie od lekarza neurologa",
            DocumentType.ZASWIADCZENIE_ENDOKRYNOLOG: "Zaświadczenie od endokrynologa/diabetologa",
            DocumentType.ZASWIADCZENIE_ONKOLOG: "Zaświadczenie od onkologa",
        }
        return descriptions.get(doc_type, "")


# Singleton instance
llm_classifier_service = LLMClassifierService()
