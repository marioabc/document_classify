Instrukcja dla developera: System klasyfikacji dokumentów medycznych

# Załozenia projektu

Efektem ma być to uruchomiony docker compose, gdzie wystawiony będzie endopint do przekazywania dokumentów, w odpowiedzi powinna być klasyfikacja każdego dokumentu.
Lista dokumentów do klasyfikacji będzie się rozwijać.

Przegląd projektu
System składa się z:

FastAPI - REST API do przyjmowania dokumentów
EasyOCR - ekstrakcja tekstu z obrazów
Classifier - klasyfikacja typów dokumentów medycznych
PostgreSQL - baza danych do przechowywania wyników
Redis - cache i kolejka zadań (opcjonalnie)
Docker Compose - orkiestracja kontenerów

Krok 1: Struktura projektu
Utwórz następującą strukturę katalogów:
medical-document-classifier/
├── app/
│ ├── **init**.py
│ ├── main.py # FastAPI application
│ ├── models.py # Pydantic models
│ ├── database.py # Database connection
│ ├── config.py # Configuration
│ ├── services/
│ │ ├── **init**.py
│ │ ├── ocr_service.py # OCR processing
│ │ ├── classifier_service.py # Document classification
│ │ └── storage_service.py # File storage
│ ├── api/
│ │ ├── **init**.py
│ │ └── endpoints.py # API endpoints
│ └── utils/
│ ├── **init**.py
│ ├── validators.py # Input validation
│ └── helpers.py # Helper functions
├── data/
│ ├── uploads/ # Temporary file storage
│ └── processed/ # Processed files
├── tests/
│ ├── **init**.py
│ ├── test_api.py
│ └── test_classifier.py
├── docker/
│ ├── Dockerfile.api
│ └── Dockerfile.worker # Opcjonalnie dla async processing
├── requirements.txt
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md

Krok 2: Utwórz pliki konfiguracyjne
2.1 requirements.txt
txtfastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==2.5.0
pydantic-settings==2.1.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.13.0
easyocr==1.7.1
pillow==10.1.0
opencv-python-headless==4.8.1.78
numpy==1.24.3
python-dotenv==1.0.0
redis==5.0.1
celery==5.3.4 # Opcjonalnie dla async
aiofiles==23.2.1
2.2 .env.example
env# Application
APP_NAME=Medical Document Classifier
APP_VERSION=1.0.0
DEBUG=True
API_PORT=8000

# Database

POSTGRES_USER=medical_user
POSTGRES_PASSWORD=secure_password_here
POSTGRES_DB=medical_docs
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis (opcjonalnie)

REDIS_HOST=redis
REDIS_PORT=6379

# OCR Settings

OCR_LANGUAGES=pl,en
OCR_GPU=False

# File Storage

MAX_FILE_SIZE=10485760 # 10MB
ALLOWED_EXTENSIONS=pdf,png,jpg,jpeg,tiff
UPLOAD_DIR=/app/data/uploads
PROCESSED_DIR=/app/data/processed

# Logging

LOG_LEVEL=INFO
2.3 docker-compose.yml
yamlversion: '3.8'

services:
api:
build:
context: .
dockerfile: docker/Dockerfile.api
container_name: medical-doc-api
ports: - "8000:8000"
environment: - POSTGRES_HOST=postgres - REDIS_HOST=redis
env_file: - .env
volumes: - ./data/uploads:/app/data/uploads - ./data/processed:/app/data/processed
depends_on: - postgres - redis
networks: - medical-network
restart: unless-stopped

postgres:
image: postgres:15-alpine
container_name: medical-doc-db
environment:
POSTGRES_USER: ${POSTGRES_USER}
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
POSTGRES_DB: ${POSTGRES_DB}
volumes: - postgres_data:/var/lib/postgresql/data
networks: - medical-network
restart: unless-stopped

redis:
image: redis:7-alpine
container_name: medical-doc-redis
networks: - medical-network
restart: unless-stopped

volumes:
postgres_data:

networks:
medical-network:
driver: bridge
2.4 docker/Dockerfile.api
dockerfileFROM python:3.11-slim

# Install system dependencies for EasyOCR and OpenCV

RUN apt-get update && apt-get install -y \
 libgl1-mesa-glx \
 libglib2.0-0 \
 libsm6 \
 libxext6 \
 libxrender-dev \
 libgomp1 \
 wget \
 && rm -rf /var/lib/apt/lists/\*

# Set working directory

WORKDIR /app

# Copy requirements and install Python dependencies

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download EasyOCR models during build (opcjonalnie, żeby przyspieszyć pierwsze uruchomienie)

RUN python -c "import easyocr; reader = easyocr.Reader(['pl', 'en'], gpu=False)"

# Copy application code

COPY app/ ./app/
COPY data/ ./data/

# Create necessary directories

RUN mkdir -p /app/data/uploads /app/data/processed

# Expose port

EXPOSE 8000

# Run the application

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

Krok 3: Implementacja kodu
3.1 app/config.py
pythonfrom pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings): # Application
APP_NAME: str = "Medical Document Classifier"
APP_VERSION: str = "1.0.0"
DEBUG: bool = True
API_PORT: int = 8000

    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    # OCR
    OCR_LANGUAGES: str = "pl,en"
    OCR_GPU: bool = False

    # File Storage
    MAX_FILE_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: str = "pdf,png,jpg,jpeg,tiff"
    UPLOAD_DIR: str = "/app/data/uploads"
    PROCESSED_DIR: str = "/app/data/processed"

    # Logging
    LOG_LEVEL: str = "INFO"

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def ocr_languages_list(self) -> List[str]:
        return [lang.strip() for lang in self.OCR_LANGUAGES.split(",")]

    @property
    def allowed_extensions_list(self) -> List[str]:
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
3.2 app/models.py
pythonfrom pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
GRUPA_KRWI = "grupa_krwi"
MORFOLOGIA = "morfologia"
APTT = "aptt"
PT_INR = "pt_inr"
INR_ANTYKOAGULANTY = "inr_antykoagulanty"
SZCZEPIENIE_WZW = "szczepienie_wzw"
POZIOM_HBS = "poziom_hbs"
ANTYGEN_HBS = "antygen_hbs"
ANTYGEN_HCV = "antygen_hcv"
KARTA_INFORMACYJNA = "karta_informacyjna"
OPIS_ZABIEGU = "opis_zabiegu"
JONOGRAM = "jonogram"
GLUKOZA = "glukoza"
KREATYNINA_MOCZNIK = "kreatynina_mocznik"
TSH_FT3_FT4 = "tsh_ft3_ft4"
RTG_KLATKA = "rtg_klatka"
EKG = "ekg"
ZASWIADCZENIE_INTERNISTA = "zaswiadczenie_internista"
ZASWIADCZENIE_KARDIOLOG = "zaswiadczenie_kardiolog"
ZASWIADCZENIE_ENDOKRYNOLOG = "zaswiadczenie_endokrynolog"
ZASWIADCZENIE_ONKOLOG = "zaswiadczenie_onkolog"
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
3.3 app/database.py
pythonfrom sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DocumentRecord(Base):
**tablename** = "documents"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    document_type = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    extracted_text = Column(Text, nullable=True)
    extracted_dates = Column(JSON, nullable=True)
    keywords_found = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    processing_time_ms = Column(Float, nullable=False)

def init_db():
Base.metadata.create_all(bind=engine)

def get_db():
db = SessionLocal()
try:
yield db
finally:
db.close()
3.4 app/services/ocr_service.py
pythonimport easyocr
import logging
from typing import List, Tuple
from PIL import Image
import numpy as np
from app.config import settings

logger = logging.getLogger(**name**)

class OCRService:
def **init**(self):
logger.info(f"Initializing EasyOCR with languages: {settings.ocr_languages_list}")
self.reader = easyocr.Reader(
settings.ocr_languages_list,
gpu=settings.OCR_GPU
)

    def extract_text(self, image_path: str) -> Tuple[str, List[str]]:
        """
        Extract text from image
        Returns: (full_text, list_of_lines)
        """
        try:
            logger.info(f"Processing image: {image_path}")

            # Read image
            image = Image.open(image_path)
            image_np = np.array(image)

            # Perform OCR
            results = self.reader.readtext(image_np, detail=0)

            # Join results
            full_text = ' '.join(results)

            logger.info(f"Extracted {len(results)} text segments")
            return full_text, results

        except Exception as e:
            logger.error(f"Error during OCR processing: {str(e)}")
            raise

    def preprocess_image(self, image_path: str) -> str:
        """
        Preprocess image for better OCR results
        Can be extended with more preprocessing steps
        """
        # Placeholder for image preprocessing
        # You can add: denoise, contrast adjustment, deskewing, etc.
        return image_path

# Singleton instance

ocr_service = OCRService()
3.5 app/services/classifier_service.py
pythonimport re
import logging
from typing import List, Tuple
from app.models import DocumentType

logger = logging.getLogger(**name**)

class DocumentClassifier:
def **init**(self): # Define classification rules
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
'jonogram', 'sód', 'potas', 'na', 'k', 'elektrolity'
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
DocumentType.ZASWIADCZENIE_ENDOKRYNOLOG: [
'zaświadczenie', 'endokrynolog', 'diabetolog', 'cukrzyca', 'endokrynologia'
],
DocumentType.ZASWIADCZENIE_ONKOLOG: [
'zaświadczenie', 'onkolog', 'onkologia', 'nowotwór'
],
}

    def classify(self, text: str) -> Tuple[DocumentType, float, List[str]]:
        """
        Classify document based on extracted text
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

        logger.info(f"Classification result: {best_match} (confidence: {best_score:.2f})")

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
3.6 app/services/storage_service.py
pythonimport os
import uuid
import shutil
import logging
from pathlib import Path
from typing import BinaryIO
from app.config import settings

logger = logging.getLogger(**name**)

class StorageService:
def **init**(self): # Create directories if they don't exist
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.PROCESSED_DIR).mkdir(parents=True, exist_ok=True)

    def save_uploaded_file(self, file: BinaryIO, filename: str) -> tuple[str, str]:
        """
        Save uploaded file to temporary storage
        Returns: (file_id, file_path)
        """
        file_id = str(uuid.uuid4())
        file_extension = Path(filename).suffix

        # Validate extension
        if file_extension.lstrip('.').lower() not in settings.allowed_extensions_list:
            raise ValueError(f"File extension {file_extension} not allowed")

        file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{file_extension}")

        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file, buffer)

            logger.info(f"File saved: {file_path}")
            return file_id, file_path

        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise

    def move_to_processed(self, file_path: str, document_type: str) -> str:
        """
        Move processed file to permanent storage
        Returns: new_file_path
        """
        try:
            filename = Path(file_path).name
            type_dir = os.path.join(settings.PROCESSED_DIR, document_type)
            Path(type_dir).mkdir(parents=True, exist_ok=True)

            new_path = os.path.join(type_dir, filename)
            shutil.move(file_path, new_path)

            logger.info(f"File moved to: {new_path}")
            return new_path

        except Exception as e:
            logger.error(f"Error moving file: {str(e)}")
            raise

    def cleanup_temp_file(self, file_path: str):
        """
        Remove temporary file
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Temporary file removed: {file_path}")
        except Exception as e:
            logger.error(f"Error removing temporary file: {str(e)}")

# Singleton instance

storage_service = StorageService()
3.7 app/api/endpoints.py
pythonfrom fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import time
import logging
from datetime import datetime

from app.models import (
DocumentUploadResponse,
BatchUploadResponse,
DocumentClassificationResult,
DocumentType
)
from app.database import get_db, DocumentRecord
from app.services.ocr_service import ocr_service
from app.services.classifier_service import classifier_service
from app.services.storage_service import storage_service
from app.config import settings

logger = logging.getLogger(**name**)
router = APIRouter()

# Required documents list

REQUIRED_DOCUMENTS = [
DocumentType.GRUPA_KRWI,
DocumentType.MORFOLOGIA,
DocumentType.APTT,
DocumentType.PT_INR,
DocumentType.EKG,
DocumentType.RTG_KLATKA,
]

@router.post("/classify", response_model=DocumentUploadResponse)
async def classify_document(
file: UploadFile = File(...),
db: Session = Depends(get_db)
):
"""
Classify a single medical document
"""
start_time = time.time()

    try:
        # Validate file size
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE} bytes"
            )

        # Save uploaded file
        file_id, file_path = storage_service.save_uploaded_file(file.file, file.filename)

        # Extract text with OCR
        logger.info(f"Processing document: {file.filename}")
        extracted_text, _ = ocr_service.extract_text(file_path)

        # Classify document
        document_type, confidence, keywords_found = classifier_service.classify(extracted_text)

        # Extract dates
        dates = classifier_service.extract_dates(extracted_text)

        # Move to processed directory
        storage_service.move_to_processed(file_path, document_type.value)

        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000

        # Create classification result
        classification = DocumentClassificationResult(
            document_type=document_type,
            confidence=confidence,
            keywords_found=keywords_found,
            extracted_text=extracted_text[:500],  # First 500 chars
            extracted_dates=dates,
            metadata={}
        )

        # Save to database
        db_record = DocumentRecord(
            id=file_id,
            filename=file.filename,
            file_size=file_size,
            document_type=document_type.value,
            confidence=confidence,
            extracted_text=extracted_text,
            extracted_dates=dates,
            keywords_found=keywords_found,
            processing_time_ms=processing_time
        )
        db.add(db_record)
        db.commit()

        response = DocumentUploadResponse(
            id=file_id,
            filename=file.filename,
            file_size=file_size,
            upload_timestamp=datetime.utcnow(),
            classification=classification,
            processing_time_ms=processing_time
        )

        logger.info(f"Document classified successfully: {document_type} ({confidence:.2f})")
        return response

    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        storage_service.cleanup_temp_file(file_path)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/classify/batch", response_model=BatchUploadResponse)
async def classify_documents_batch(
files: List[UploadFile] = File(...),
db: Session = Depends(get_db)
):
"""
Classify multiple medical documents and check completeness
"""
results = []
failed = 0

    for file in files:
        try:
            result = await classify_document(file, db)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process {file.filename}: {str(e)}")
            failed += 1

    # Check for missing required documents
    classified_types = [r.classification.document_type for r in results]
    missing_docs = [
        doc.value for doc in REQUIRED_DOCUMENTS
        if doc not in classified_types
    ]

    completeness = ((len(REQUIRED_DOCUMENTS) - len(missing_docs)) / len(REQUIRED_DOCUMENTS)) * 100

    return BatchUploadResponse(
        total_documents=len(files),
        successfully_processed=len(results),
        failed=failed,
        results=results,
        missing_required_documents=missing_docs,
        completeness_percentage=completeness
    )

@router.get("/documents/{document_id}")
async def get_document_details(document_id: str, db: Session = Depends(get_db)):
"""
Get details of a specific document
"""
record = db.query(DocumentRecord).filter(DocumentRecord.id == document_id).first()

    if not record:
        raise HTTPException(status_code=404, detail="Document not found")

    return record

@router.get("/documents")
async def list_documents(
skip: int = 0,
limit: int = 100,
document_type: str = None,
db: Session = Depends(get_db)
):
"""
List all processed documents
"""
query = db.query(DocumentRecord)

    if document_type:
        query = query.filter(DocumentRecord.document_type == document_type)

    records = query.offset(skip).limit(limit).all()
    return records

3.8 app/main.py
pythonfrom fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime

from app.api.endpoints import router
from app.database import init_db
from app.models import HealthCheckResponse
from app.config import settings

# Configure logging

logging.basicConfig(
level=getattr(logging, settings.LOG_LEVEL),
format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(**name**)

# Create FastAPI app

app = FastAPI(
title=settings.APP_NAME,
version=settings.APP_VERSION,
description="API for classifying medical documents using OCR and ML"
)

# Configure CORS

app.add_middleware(
CORSMiddleware,
allow_origins=["*"],
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
)

# Include routers

app.include_router(router, prefix="/api/v1", tags=["documents"])

@app.on_event("startup")
async def startup_event():
"""Initialize database on startup"""
logger.info("Starting application...")
init_db()
logger.info("Database initialized")

@app.get("/", response_model=HealthCheckResponse)
async def health_check():
"""Health check endpoint"""
return HealthCheckResponse(
status="healthy",
version=settings.APP_VERSION,
timestamp=datetime.utcnow()
)

@app.get("/health")
async def health():
"""Simple health check"""
return {"status": "ok"}

if **name** == "**main**":
import uvicorn
uvicorn.run(
"app.main:app",
host="0.0.0.0",
port=settings.API_PORT,
reload=settings.DEBUG
)

Krok 4: Testy
4.1 tests/test_api.py
pythonfrom fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
response = client.get("/")
assert response.status_code == 200
assert response.json()["status"] == "healthy"

def test_classify_document(): # Mock file upload
with open("test_document.png", "rb") as f:
response = client.post(
"/api/v1/classify",
files={"file": ("test.png", f, "image/png")}
)

    assert response.status_code == 200
    data = response.json()
    assert "classification" in data
    assert "document_type" in data["classification"]

Krok 5: Uruchomienie
5.1 Skopiuj .env.example do .env i dostosuj wartości
bashcp .env.example .env
5.2 Build i uruchom kontenery
bash# Build
docker-compose build

# Uruchom

docker-compose up -d

# Sprawdź logi

docker-compose logs -f api
5.3 Sprawdź czy API działa
bash# Health check
curl http://localhost:8000/health

# Test klasyfikacji

curl -X POST "http://localhost:8000/api/v1/classify" \
 -H "accept: application/json" \
 -H "Content-Type: multipart/form-data" \
 -F "file=@/path/to/document.jpg"

Krok 6: Testowanie z przykładowymi dokumentami
6.1 Przykład Python client
pythonimport requests

# Single document

with open("document.jpg", "rb") as f:
files = {"file": f}
response = requests.post(
"http://localhost:8000/api/v1/classify",
files=files
)
print(response.json())

# Batch upload

files = [
("files", open("doc1.jpg", "rb")),
("files", open("doc2.jpg", "rb")),
("files", open("doc3.jpg", "rb"))
]
response = requests.post(
"http://localhost:8000/api/v1/classify/batch",
files=files
)
print(response.json())

Krok 7: Monitoring i debugowanie
7.1 Sprawdź logi
bash# API logs
docker-compose logs -f api

# Database logs

docker-compose logs -f postgres

# All logs

docker-compose logs -f
7.2 Wejdź do kontenera
bash# API container
docker-compose exec api bash

# Database

docker-compose exec postgres psql -U medical_user -d medical_docs

Krok 8: Rozszerzenia (opcjonalne)
8.1 Dodaj Swagger UI
FastAPI automatycznie generuje dokumentację:

http://localhost:8000/docs (Swagger)
http://localhost:8000/redoc (ReDoc)

8.2 Dodaj autentykację
python# app/auth.py
from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME)

async def get_api_key(api_key: str = Security(api_key_header)):
if api_key != settings.API_KEY:
raise HTTPException(status_code=403, detail="Invalid API Key")
return api_key
8.3 Dodaj async processing z Celery
python# app/tasks.py
from celery import Celery

celery_app = Celery(
'tasks',
broker=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0'
)

@celery_app.task
def process_document_async(file_path: str): # Process document in background
pass

Checklist dla developera

Sklonuj repozytorium / utwórz strukturę
Utwórz wszystkie pliki z kodem
Skopiuj .env.example do .env
Dostosuj zmienne środowiskowe w .env
Zbuduj obrazy Docker: docker-compose build
Uruchom kontenery: docker-compose up -d
Sprawdź health check: curl http://localhost:8000/health
Przetestuj endpoint /api/v1/classify z przykładowym dokumentem
Sprawdź logi: docker-compose logs -f
Zweryfikuj, że dokumenty są zapisywane w bazie danych
Przetestuj batch upload
Sprawdź dokumentację API: http://localhost:8000/docs
Napisz testy jednostkowe
Dodaj monitoring (opcjonalnie)

Troubleshooting
Problem: EasyOCR nie pobiera modeli
Rozwiązanie: Dodaj do Dockerfile pobieranie modeli podczas buildu
Problem: Out of memory podczas OCR
Rozwiązanie: Zwiększ pamięć kontenera lub zmniejsz rozdzielczość obrazów
Problem: Wolne przetwarzanie
Rozwiązanie:

Włącz GPU w OCR (jeśli dostępne)
Dodaj Redis cache
Użyj async processing z Celery

Problem: Błędy połączenia z PostgreSQL
Rozwiązanie: Sprawdź czy kontener postgres jest uruchomiony i zmienne w .env są poprawne
