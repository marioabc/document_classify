from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    GRUPA_KRWI = "DOC_BADANIE_RH"
    MORFOLOGIA = "DOC_BADANIE_MORF"
    APTT = "DOC_BADANIE_APTT"
    PT_INR = "DOC_BADANIE_PTINR"
    INR_ANTYKOAGULANTY = "DOC_BADANIE_INR"
    SZCZEPIENIE_WZW = "DOC_BADANIE_WZWB"
    POZIOM_HBS = "DOC_BADANIE_HBS"
    ANTYGEN_HBS = "DOC_BADANIE_ANTYHBS"
    ANTYGEN_HCV = "DOC_BADANIE_ANTYHCV"
    KARTA_INFORMACYJNA = "DOC_BADANIE_KISZP"
    OPIS_ZABIEGU = "DOC_BADANIE_OPZAB"
    JONOGRAM = "DOC_BADANIE_JONONAK"
    GLUKOZA = "DOC_BADANIE_GLUK"
    KREATYNINA_MOCZNIK = "DOC_BADANIE_KREMOC"
    TSH_FT3_FT4 = "DOC_BADANIE_TSH"
    RTG_KLATKA = "DOC_BADANIE_RTGKP"
    EKG = "DOC_BADANIE_EKG"
    ZASWIADCZENIE_INTERNISTA = "DOC_BADANIE_INTERN"
    ZASWIADCZENIE_KARDIOLOG = "DOC_BADANIE_LK"
    ZASWIADCZENIE_NEUROLOG = "DOC_BADANIE_LN"
    ZASWIADCZENIE_ENDOKRYNOLOG = "DOC_BADANIE_ZASEND"
    ZASWIADCZENIE_ONKOLOG = "DOC_BADANIE_ZASONK"
    INNE = "inne"


class DocumentClassificationResult(BaseModel):
    document_type: DocumentType
    confidence: float = Field(..., ge=0.0, le=1.0)
    keywords_found: List[str]
    extracted_text: Optional[str] = None
    extracted_dates: List[str] = []
    metadata: Optional[Dict] = {}


class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    file_size: int
    upload_timestamp: datetime
    classification: DocumentClassificationResult
    processing_time_ms: float


class BatchUploadResponse(BaseModel):
    total_documents: int
    successfully_processed: int
    failed: int
    results: List[DocumentUploadResponse]
    missing_required_documents: List[str]
    completeness_percentage: float


class HealthCheckResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
