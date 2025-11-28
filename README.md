# Medical Document Classifier

System do klasyfikacji dokumentów medycznych wykorzystujący OCR (EasyOCR) i algorytmy klasyfikacji oparte na słowach kluczowych.

## Opis projektu

System automatycznie klasyfikuje dokumenty medyczne na podstawie wyekstrahowanego tekstu. Wykorzystuje FastAPI do obsługi REST API, EasyOCR do ekstrakcji tekstu z obrazów oraz PostgreSQL do przechowywania wyników.

### Funkcjonalności

- ✅ Klasyfikacja 23 typów dokumentów medycznych
- ✅ Ekstrakcja tekstu z obrazów (OCR)
- ✅ Wykrywanie dat w różnych formatach (polskie i ISO)
- ✅ Batch upload - przetwarzanie wielu dokumentów naraz
- ✅ Sprawdzanie kompletności dokumentacji
- ✅ API REST z dokumentacją Swagger
- ✅ Przechowywanie wyników w PostgreSQL
- ✅ Redis do cache i kolejki zadań

### Wspierane typy dokumentów

- Grupa krwi
- Morfologia krwi
- APTT (czas częściowej tromboplastyny)
- PT/INR (czas protrombinowy)
- INR dla antykoagulantów
- Szczepienie WZW
- Poziom przeciwciał HBS
- Antygen HBS/HCV
- Karta informacyjna szpitala
- Opis zabiegu operacyjnego
- Jonogram (elektrolity)
- Glukoza
- Kreatynina i mocznik
- TSH, FT3, FT4 (tarczyca)
- RTG klatki piersiowej
- EKG
- Zaświadczenia specjalistyczne (internista, kardiolog, endokrynolog, onkolog)

## Wymagania

- Docker i Docker Compose
- 4GB RAM (zalecane 8GB)
- 5GB wolnego miejsca na dysku

## Instalacja i uruchomienie

### 1. Klonowanie repozytorium

```bash
git clone <repository-url>
cd klasyfikacja_dokumentow
```

### 2. Konfiguracja zmiennych środowiskowych

```bash
cp .env.example .env
```

Edytuj plik `.env` i dostosuj wartości (szczególnie hasła):

```env
POSTGRES_USER=medical_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=medical_docs
```

### 3. Budowanie i uruchomienie

```bash
# Zbuduj obrazy Docker
docker-compose build

# Uruchom kontenery
docker-compose up -d

# Sprawdź logi
docker-compose logs -f api
```

### 4. Sprawdzenie działania

```bash
# Health check
curl http://localhost:8000/health

# Dokumentacja API
open http://localhost:8000/docs
```

## Użycie API

### Klasyfikacja pojedynczego dokumentu

```bash
curl -X POST "http://localhost:8000/api/v1/classify" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/document.jpg"
```

**Odpowiedź:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.jpg",
  "file_size": 245678,
  "upload_timestamp": "2024-11-27T10:30:00",
  "classification": {
    "document_type": "morfologia",
    "confidence": 0.85,
    "keywords_found": ["morfologia", "wbc", "rbc", "hemoglobina"],
    "extracted_text": "Morfologia krwi: WBC 7.5...",
    "extracted_dates": ["15.11.2024"],
    "metadata": {}
  },
  "processing_time_ms": 2341.5
}
```

### Klasyfikacja wielu dokumentów (batch)

```bash
curl -X POST "http://localhost:8000/api/v1/classify/batch" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@doc1.jpg" \
  -F "files=@doc2.jpg" \
  -F "files=@doc3.jpg"
```

**Odpowiedź:**
```json
{
  "total_documents": 3,
  "successfully_processed": 3,
  "failed": 0,
  "results": [...],
  "missing_required_documents": ["ekg", "rtg_klatka"],
  "completeness_percentage": 66.67
}
```

### Lista dokumentów

```bash
# Wszystkie dokumenty
curl http://localhost:8000/api/v1/documents

# Z filtrowaniem i paginacją
curl "http://localhost:8000/api/v1/documents?document_type=morfologia&skip=0&limit=10"
```

### Szczegóły dokumentu

```bash
curl http://localhost:8000/api/v1/documents/{document_id}
```

## Użycie w Pythonie

```python
import requests

# Klasyfikacja pojedynczego dokumentu
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
```

## Struktura projektu

```
klasyfikacja_dokumentow/
├── app/
│   ├── config.py              # Konfiguracja aplikacji
│   ├── models.py              # Modele Pydantic
│   ├── database.py            # Konfiguracja bazy danych
│   ├── main.py                # Główna aplikacja FastAPI
│   ├── services/
│   │   ├── ocr_service.py     # Serwis OCR (EasyOCR)
│   │   ├── classifier_service.py  # Klasyfikacja dokumentów
│   │   └── storage_service.py     # Zarządzanie plikami
│   └── api/
│       └── endpoints.py       # Endpointy API
├── data/
│   ├── uploads/               # Pliki tymczasowe
│   └── processed/             # Przetworzone pliki
├── tests/
│   ├── test_api.py           # Testy API
│   └── test_classifier.py    # Testy klasyfikatora
├── docker/
│   └── Dockerfile.api        # Dockerfile dla API
├── docker-compose.yml        # Orkiestracja kontenerów
├── requirements.txt          # Zależności Python
└── .env                      # Zmienne środowiskowe
```

## Testowanie

```bash
# Uruchom testy w kontenerze
docker-compose exec api pytest

# Z pokryciem kodu
docker-compose exec api pytest --cov=app tests/

# Tylko testy API
docker-compose exec api pytest tests/test_api.py

# Tylko testy klasyfikatora
docker-compose exec api pytest tests/test_classifier.py
```

## Dokumentacja API

Po uruchomieniu aplikacji, dokumentacja API jest dostępna pod adresami:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Zarządzanie kontenerami

```bash
# Uruchomienie
docker-compose up -d

# Zatrzymanie
docker-compose down

# Restart
docker-compose restart

# Logi
docker-compose logs -f api
docker-compose logs -f postgres

# Wejście do kontenera
docker-compose exec api bash
docker-compose exec postgres psql -U medical_user -d medical_docs
```

## Troubleshooting

### Problem: EasyOCR nie pobiera modeli
**Rozwiązanie**: Modele są pobierane podczas budowania obrazu. Jeśli wystąpił błąd, usuń obraz i zbuduj ponownie:
```bash
docker-compose down
docker rmi klasyfikacja_dokumentow-api
docker-compose build --no-cache
```

### Problem: Out of memory podczas OCR
**Rozwiązanie**: Zwiększ pamięć dostępną dla Docker lub zmniejsz rozdzielczość obrazów przed wysłaniem.

### Problem: Błędy połączenia z PostgreSQL
**Rozwiązanie**: Sprawdź czy kontener postgres jest uruchomiony:
```bash
docker-compose ps
docker-compose logs postgres
```

### Problem: Wolne przetwarzanie
**Rozwiązanie**:
- Włącz GPU w OCR (jeśli dostępne): zmień `OCR_GPU=True` w `.env`
- Rozważ dodanie Redis cache
- Użyj async processing z Celery (opcjonalnie)

## Konfiguracja

Wszystkie ustawienia znajdują się w pliku `.env`:

| Zmienna | Opis | Domyślna wartość |
|---------|------|------------------|
| `APP_NAME` | Nazwa aplikacji | Medical Document Classifier |
| `API_PORT` | Port API | 8000 |
| `POSTGRES_USER` | Użytkownik PostgreSQL | medical_user |
| `POSTGRES_PASSWORD` | Hasło PostgreSQL | - |
| `OCR_LANGUAGES` | Języki OCR (oddzielone przecinkami) | pl,en |
| `OCR_GPU` | Użycie GPU dla OCR | False |
| `MAX_FILE_SIZE` | Maks. rozmiar pliku (bajty) | 10485760 (10MB) |
| `ALLOWED_EXTENSIONS` | Dozwolone rozszerzenia | pdf,png,jpg,jpeg,tiff |
| `LOG_LEVEL` | Poziom logowania | INFO |

## Rozszerzenia (opcjonalne)

### Dodanie autentykacji API Key

Edytuj `app/api/endpoints.py` i dodaj weryfikację API Key.

### Async processing z Celery

Dla dużych wolumenów dokumentów można dodać Celery worker do przetwarzania w tle.

### Monitoring i metryki

Rozważ dodanie Prometheus i Grafana do monitorowania wydajności.

## Licencja

MIT License

## Kontakt

W razie pytań lub problemów, otwórz issue w repozytorium.
