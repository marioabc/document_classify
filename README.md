# Medical Document Classifier

System do klasyfikacji dokumentów medycznych wykorzystujący OCR (EasyOCR) i inteligentny klasyfikator oparty na LLM (Ollama).

## Opis projektu

System automatycznie klasyfikuje dokumenty medyczne na podstawie wyekstrahowanego tekstu. Wykorzystuje FastAPI do obsługi REST API, EasyOCR do ekstrakcji tekstu z obrazów, lokalny model LLM (Ollama) do inteligentnej klasyfikacji oraz PostgreSQL do przechowywania wyników.

### Funkcjonalności

- ✅ **Klasyfikacja 23 typów dokumentów medycznych** z użyciem AI
- ✅ **Inteligentny klasyfikator LLM** (Ollama) - rozumie kontekst, nie tylko słowa kluczowe
- ✅ **Ekstrakcja tekstu z obrazów** (OCR) - wsparcie dla polskiego języka
- ✅ **Merged document processing** - sklej wiele stron w jeden dokument
- ✅ **Asynchroniczne przetwarzanie** - callback po zakończeniu klasyfikacji
- ✅ **Wykrywanie dat** w różnych formatach (polskie i ISO)
- ✅ **Batch upload** - przetwarzanie wielu dokumentów naraz
- ✅ **Sprawdzanie kompletności** dokumentacji
- ✅ **API REST z dokumentacją Swagger**
- ✅ **Przechowywanie wyników** w PostgreSQL
- ✅ **Redis** do cache i kolejki zadań

### Wspierane typy dokumentów

System rozpoznaje **23 typy dokumentów medycznych**:

#### Badania laboratoryjne

- `DOC_BADANIE_RH` - Grupa krwi + RH
- `DOC_BADANIE_MORF` - Morfologia krwi
- `DOC_BADANIE_APTT` - APTT (czas częściowej tromboplastyny)
- `DOC_BADANIE_PTINR` - PT + INR (czas protrombinowy)
- `DOC_BADANIE_INR` - INR dla antykoagulantów
- `DOC_BADANIE_JONONAK` - Jonogram (elektrolity: Na, K)
- `DOC_BADANIE_GLUK` - Glukoza na czczo
- `DOC_BADANIE_KREMOC` - Kreatynina i mocznik
- `DOC_BADANIE_TSH` - TSH, FT3, FT4 (tarczyca)

#### Badania wirusologiczne

- `DOC_BADANIE_WZWB` - Szczepienie przeciw WZW typ B
- `DOC_BADANIE_HBS` - Poziom przeciwciał HBS
- `DOC_BADANIE_ANTYHBS` - Antygen HBS
- `DOC_BADANIE_ANTYHCV` - Antygen HCV

#### Badania obrazowe i diagnostyczne

- `DOC_BADANIE_RTGKP` - RTG klatki piersiowej
- `DOC_BADANIE_EKG` - EKG spoczynkowe

#### Dokumentacja medyczna

- `DOC_BADANIE_KISZP` - Karta informacyjna z pobytu szpitalnego
- `DOC_BADANIE_OPZAB` - Opis zabiegu operacyjnego

#### Zaświadczenia specjalistyczne

- `DOC_BADANIE_INTERN` - Zaświadczenie od internisty/pediatry
- `DOC_BADANIE_LK` - Zaświadczenie od kardiologa
- `DOC_BADANIE_LN` - Zaświadczenie od neurologa
- `DOC_BADANIE_ZASEND` - Zaświadczenie od endokrynologa/diabetologa
- `DOC_BADANIE_ZASONK` - Zaświadczenie od onkologa

#### Inne

- `inne` - Dokumenty niepasujące do powyższych kategorii

## Wymagania

- Docker 20.10+ i Docker Compose 2.0+
- **4GB RAM** (zalecane **8GB** dla Ollama)
- **20GB** wolnego miejsca na dysku (modele LLM + dane)
- System operacyjny: Linux, macOS lub Windows z WSL2
- (Opcjonalnie) GPU NVIDIA dla szybszego OCR i LLM

## Jak działa klasyfikator?

System wykorzystuje **dwupoziomową klasyfikację**:

### 1. **Klasyfikator LLM (Ollama)** - główny

- Używa lokalnego modelu językowego (domyślnie `llama3.2:3b`)
- **Rozumie kontekst**, nie tylko słowa kluczowe
- Radzi sobie z **błędami OCR**
- Zwraca typ dokumentu + poziom pewności + uzasadnienie
- Jeśli niedostępny lub pewność < 0.5 → fallback do reguł

### 2. **Klasyfikator oparty na regułach** - fallback

- Wyszukuje słowa kluczowe w tekście
- Szybki, ale mniej dokładny
- Używany gdy LLM jest niedostępny

**Przykład:**

```
Tekst: "ZAŚWIADCZENIE O SZCZEPIENIU PRZECIW WZW TYPU B"

❌ Klasyfikator reguł:
   - Znalazł słowo "zaświadczenie"
   - Sklasyfikował jako "DOC_BADANIE_INTERN" (błąd!)

✅ Klasyfikator LLM:
   - Zrozumiał kontekst "szczepienie WZW"
   - Sklasyfikował jako "DOC_BADANIE_WZWB" (poprawnie!)
   - Pewność: 0.95
```

Szczegóły: Zobacz `LLM_CLASSIFIER_README.md`

## Instalacja i uruchomienie

### 1. Klonowanie repozytorium

```bash
git clone https://github.com/marioabc/document_classify.git
cd document_classify
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

### Endpoint 1: Klasyfikacja pojedynczego dokumentu

**POST** `/classify`

Klasyfikuje pojedynczy plik medyczny.

```bash
curl -X POST "http://localhost:8000/classify" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.jpg"
```

**Response (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.jpg",
  "file_size": 245678,
  "upload_timestamp": "2024-11-28T10:30:00",
  "classification": {
    "document_type": "DOC_BADANIE_MORF",
    "confidence": 0.95,
    "keywords_found": ["morfologia", "wbc", "rbc"],
    "extracted_text": "Morfologia krwi: WBC 7.5, RBC 4.8...",
    "extracted_dates": ["15.11.2024"],
    "metadata": {}
  },
  "processing_time_ms": 2341.5
}
```

---

### Endpoint 2: Klasyfikacja połączonych plików (synchroniczna)

**POST** `/classify/merged`

Klasyfikuje wiele plików jako JEDEN dokument (np. dokument wielostronicowy zeskanowany jako osobne pliki). Zwraca wynik po zakończeniu przetwarzania.

```bash
curl -X POST "http://localhost:8000/classify/merged" \
  -F "files=@page1.jpg" \
  -F "files=@page2.jpg" \
  -F "files=@page3.jpg"
```

**Response (200 OK):**

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "filename": "merged_3_files",
  "file_size": 892456,
  "upload_timestamp": "2024-11-28T10:32:00",
  "classification": {
    "document_type": "DOC_BADANIE_LK",
    "confidence": 0.92,
    "keywords_found": ["zaświadczenie", "kardiolog"],
    "extracted_text": "ZAŚWIADCZENIE KARDIOLOGICZNE...",
    "extracted_dates": ["20.11.2024"],
    "metadata": {
      "merged_files": ["page1.jpg", "page2.jpg", "page3.jpg"],
      "total_files": 3
    }
  },
  "processing_time_ms": 4567.8
}
```

**Use case:** Dokument został zeskanowany jako 3 osobne pliki JPG (strona 1, 2, 3), ale chcesz klasyfikować go jako jeden dokument.

---

### Endpoint 3: Klasyfikacja połączonych plików (asynchroniczna z callbackiem)

**POST** `/classify/merged/async`

**NOWY!** Asynchroniczne przetwarzanie - zwraca natychmiastową odpowiedź (201), a po zakończeniu klasyfikacji wysyła wynik przez POST callback do zewnętrznego API.

```bash
curl -X POST "http://localhost:8000/classify/merged/async" \
  -F "recipeId=DOC_BADANIE_LK" \
  -F "elementId=12345" \
  -F "files=@page1.jpg" \
  -F "files=@page2.jpg"
```

**Parametry multipart/form-data:**

- `recipeId` (string, required) - Oczekiwany typ dokumentu (np. `DOC_BADANIE_LK`)
- `elementId` (string, required) - Identyfikator elementu w zewnętrznym systemie
- `files` (files, required) - Pliki do sklasyfikowania (co najmniej 1)

**Response (201 Created - natychmiastowa):**

```json
{
  "status": "accepted",
  "message": "Document processing started",
  "recipeId": "DOC_BADANIE_LK",
  "elementId": "12345",
  "filesCount": 2
}
```

**Callback (wykonywany PO klasyfikacji):**

System automatycznie wyśle POST request do:

```
POST http://localhost:9091/public/api/v1/checklists/elements/{elementId}/ai-validate
Content-Type: application/json

{
  "classifyDocumentType": "DOC_BADANIE_LK",
  "classifyConfidence": 0.95,
  "confidence": 1.0,
  "recipeId": "DOC_BADANIE_LK"
}
```

**Logika obliczania `confidence`:**

- Jeśli `recipeId` == `classify_document_type` AND `classify_confidence` > 75%: `confidence = 1.0`
- Jeśli `recipeId` == `classify_document_type` AND `classify_confidence` 50-75%: `confidence = 0.5`
- Jeśli `recipeId` == `classify_document_type` AND `classify_confidence` < 50%: `confidence = 0.0`
- Jeśli `recipeId` != `classify_document_type`: `confidence = 0.0` (niezależnie od classify_confidence)

**Use case:**

- Integracja z zewnętrznym systemem (np. systemem checklist)
- Nie chcesz czekać na zakończenie przetwarzania (OCR może trwać kilka sekund)
- Zewnętrzny system otrzyma wynik automatycznie przez callback
- Weryfikacja zgodności sklasyfikowanego typu z oczekiwanym (recipeId)

---

### Endpoint 4: Klasyfikacja wielu dokumentów (batch)

**POST** `/classify/batch`

Klasyfikuje wiele niezależnych dokumentów i zwraca wyniki dla każdego z nich. Sprawdza też kompletność dokumentacji.

```bash
curl -X POST "http://localhost:8000/classify/batch" \
  -F "files=@grupa_krwi.jpg" \
  -F "files=@morfologia.jpg" \
  -F "files=@ekg.jpg"
```

**Response (200 OK):**

```json
{
  "total_documents": 3,
  "successfully_processed": 3,
  "failed": 0,
  "results": [
    {
      "id": "...",
      "filename": "grupa_krwi.jpg",
      "classification": {
        "document_type": "DOC_BADANIE_RH",
        "confidence": 0.98
      }
    },
    {
      "id": "...",
      "filename": "morfologia.jpg",
      "classification": {
        "document_type": "DOC_BADANIE_MORF",
        "confidence": 0.95
      }
    },
    {
      "id": "...",
      "filename": "ekg.jpg",
      "classification": {
        "document_type": "DOC_BADANIE_EKG",
        "confidence": 0.93
      }
    }
  ],
  "missing_required_documents": [
    "DOC_BADANIE_APTT",
    "DOC_BADANIE_PTINR",
    "DOC_BADANIE_RTGKP"
  ],
  "completeness_percentage": 50.0
}
```

**Use case:** Upload wielu różnych dokumentów naraz z analizą kompletności.

## Użycie w Pythonie

### Przykład 1: Pojedynczy dokument

```python
import requests

# Klasyfikacja pojedynczego dokumentu
with open("document.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:8000/classify",
        files={"file": f}
    )
    result = response.json()
    print(f"Typ: {result['classification']['document_type']}")
    print(f"Pewność: {result['classification']['confidence']}")
```

### Przykład 2: Dokument wielostronicowy (synchroniczny)

```python
import requests

# Sklej 3 strony w jeden dokument
files = [
    ("files", open("page1.jpg", "rb")),
    ("files", open("page2.jpg", "rb")),
    ("files", open("page3.jpg", "rb"))
]

response = requests.post(
    "http://localhost:8000/classify/merged",
    files=files
)

result = response.json()
print(f"Połączono {result['classification']['metadata']['total_files']} plików")
print(f"Typ: {result['classification']['document_type']}")
```

### Przykład 3: Asynchroniczny z callbackiem

```python
import requests

# Wyślij do przetwarzania asynchronicznego
data = {
    "recipeId": "DOC_BADANIE_LK",
    "elementId": "12345"
}

files = [
    ("files", open("page1.jpg", "rb")),
    ("files", open("page2.jpg", "rb"))
]

response = requests.post(
    "http://localhost:8000/classify/merged/async",
    data=data,
    files=files
)

# Natychmiastowa odpowiedź (201)
print(response.json())
# {"status": "accepted", "recipeId": "DOC_BADANIE_LK", "elementId": "12345", "filesCount": 2}

# Wynik zostanie wysłany callbackiem do:
# POST http://localhost:9091/public/api/v1/checklists/elements/12345/ai-validate
# Payload: {
#   "classify_document_type": "DOC_BADANIE_LK",
#   "classify_confidence": 0.95,
#   "confidence": 1.0,  # obliczone na podstawie zgodności recipeId
#   "recipe_id": "DOC_BADANIE_LK"
# }
```

### Przykład 4: Batch upload z analizą kompletności

```python
import requests

# Upload wielu różnych dokumentów
files = [
    ("files", open("grupa_krwi.jpg", "rb")),
    ("files", open("morfologia.jpg", "rb")),
    ("files", open("ekg.jpg", "rb"))
]

response = requests.post(
    "http://localhost:8000/classify/batch",
    files=files
)

result = response.json()
print(f"Przetworzono: {result['successfully_processed']}/{result['total_documents']}")
print(f"Kompletność: {result['completeness_percentage']}%")
print(f"Brakuje: {result['missing_required_documents']}")
```

### Przykład 5: Obsługa błędów

```python
import requests

try:
    with open("document.jpg", "rb") as f:
        response = requests.post(
            "http://localhost:8000/classify",
            files={"file": f},
            timeout=30
        )

    if response.status_code == 200:
        result = response.json()
        print(f"Sukces: {result['classification']['document_type']}")
    elif response.status_code == 400:
        print(f"Błąd walidacji: {response.json()['detail']}")
    else:
        print(f"Błąd serwera: {response.status_code}")

except requests.exceptions.Timeout:
    print("Timeout - OCR trwa zbyt długo")
except requests.exceptions.ConnectionError:
    print("Nie można połączyć się z API")
```

## Struktura projektu

```
document_classify/
├── app/
│   ├── config.py                      # Konfiguracja aplikacji
│   ├── models.py                      # Modele Pydantic (23 typy dokumentów)
│   ├── database.py                    # Konfiguracja bazy danych
│   ├── main.py                        # Główna aplikacja FastAPI
│   ├── services/
│   │   ├── ocr_service.py             # Serwis OCR (EasyOCR)
│   │   ├── classifier_service.py      # Główny klasyfikator (LLM + fallback)
│   │   ├── llm_classifier_service.py  # Klasyfikator LLM (Ollama)
│   │   └── storage_service.py         # Zarządzanie plikami
│   └── api/
│       └── endpoints.py               # 4 endpointy API + callback
├── data/
│   ├── uploads/                       # Pliki tymczasowe
│   └── processed/                     # Przetworzone pliki (po typach)
├── tests/
│   ├── test_api.py                    # Testy API
│   └── test_classifier.py             # Testy klasyfikatora
├── docker/
│   ├── Dockerfile.api                 # Dockerfile dla API
│   └── init-ollama.sh                 # Skrypt inicjalizacji Ollama
├── docker-compose.yml                 # Orkiestracja (API, Postgres, Redis, Ollama)
├── requirements.txt                   # Zależności Python
├── .env                               # Zmienne środowiskowe
├── .env.example                       # Przykład konfiguracji
├── .dockerignore                      # Pliki ignorowane przez Docker
├── README.md                          # Ta dokumentacja
├── DEPLOYMENT.md                      # Instrukcja deploymentu produkcyjnego
├── DEPLOYMENT_CHECKLIST.md            # Szybki checklist deploymentu
└── LLM_CLASSIFIER_README.md           # Dokumentacja klasyfikatora LLM
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

## Podsumowanie endpointów API

| Endpoint                 | Metoda | Opis                                 | Parametry                          | Zwraca wynik              |
| ------------------------ | ------ | ------------------------------------ | ---------------------------------- | ------------------------- |
| `/classify`              | POST   | Klasyfikuj jeden plik                | `file`                             | Synchronicznie (200)      |
| `/classify/merged`       | POST   | Sklej wiele plików w jeden dokument  | `files[]`                          | Synchronicznie (200)      |
| `/classify/merged/async` | POST   | Sklej + callback po zakończeniu      | `recipeId`, `elementId`, `files[]` | **Asynchronicznie (201)** |
| `/classify/batch`        | POST   | Klasyfikuj wiele osobnych dokumentów | `files[]`                          | Synchronicznie (200)      |

## Dokumentacja API

Po uruchomieniu aplikacji, dokumentacja API jest dostępna pod adresami:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health check**: http://localhost:8000/health

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

### Problem: Ollama nie pobiera modelu

**Rozwiązanie**: Model pobiera się automatycznie przy pierwszym uruchomieniu. Sprawdź logi:

```bash
docker-compose logs ollama-init
docker-compose logs ollama

# Ręcznie pobierz model
docker-compose exec ollama ollama pull llama3.2:3b

# Sprawdź dostępne modele
docker-compose exec ollama ollama list
```

### Problem: Niska dokładność klasyfikacji

**Rozwiązanie**: Zmień model na większy w `.env`:

```bash
OLLAMA_MODEL=llama3.2:7b  # lub mistral
```

Następnie:

```bash
docker-compose restart ollama
docker-compose exec ollama ollama pull llama3.2:7b
```

### Problem: EasyOCR nie pobiera modeli

**Rozwiązanie**: Modele są pobierane podczas budowania obrazu. Jeśli wystąpił błąd:

```bash
docker-compose down
docker rmi document_classify-api
docker-compose build --no-cache api
```

### Problem: Out of memory podczas przetwarzania

**Rozwiązanie**:

- Zwiększ pamięć Docker do 8GB (dla Ollama)
- Użyj mniejszego modelu: `OLLAMA_MODEL=llama3.2:1b`
- Zmniejsz rozdzielczość obrazów przed wysłaniem

### Problem: Błędy połączenia z PostgreSQL

**Rozwiązanie**:

```bash
docker-compose ps
docker-compose logs postgres
# Sprawdź czy kontener działa
```

### Problem: Wolne przetwarzanie

**Rozwiązanie**:

- **GPU**: Włącz `OCR_GPU=True` w `.env` (wymaga NVIDIA GPU)
- **Model**: Użyj mniejszego modelu Ollama (`llama3.2:1b`)
- **Workers**: Zwiększ liczbę workerów w `docker/Dockerfile.api`
- **Async**: Użyj endpointa `/classify/merged/{element_id}` dla dużych plików

### Problem: Callback nie działa

**Rozwiązanie**:

```bash
# Sprawdź logi API
docker-compose logs api | grep "callback"

# Sprawdź czy URL zewnętrznego API jest osiągalny z kontenera
docker-compose exec api curl http://app:9091/health
```

## Konfiguracja

Wszystkie ustawienia znajdują się w pliku `.env`:

### Podstawowe ustawienia

| Zmienna       | Opis                               | Domyślna wartość            |
| ------------- | ---------------------------------- | --------------------------- |
| `APP_NAME`    | Nazwa aplikacji                    | Medical Document Classifier |
| `APP_VERSION` | Wersja aplikacji                   | 1.0.0                       |
| `DEBUG`       | Tryb debug (ustaw `False` w prod!) | True                        |
| `API_PORT`    | Port API                           | 8000                        |
| `LOG_LEVEL`   | Poziom logowania                   | INFO                        |

### Baza danych

| Zmienna             | Opis                  | Domyślna wartość |
| ------------------- | --------------------- | ---------------- |
| `POSTGRES_USER`     | Użytkownik PostgreSQL | medical_user     |
| `POSTGRES_PASSWORD` | Hasło PostgreSQL      | **ZMIEŃ!**       |
| `POSTGRES_DB`       | Nazwa bazy            | medical_docs     |
| `POSTGRES_HOST`     | Host bazy             | postgres         |

### OCR (EasyOCR)

| Zmienna         | Opis                                | Domyślna wartość |
| --------------- | ----------------------------------- | ---------------- |
| `OCR_LANGUAGES` | Języki OCR (oddzielone przecinkami) | pl,en            |
| `OCR_GPU`       | Użycie GPU dla OCR                  | False            |

### LLM Classifier (Ollama)

| Zmienna        | Opis                  | Domyślna wartość    |
| -------------- | --------------------- | ------------------- |
| `OLLAMA_URL`   | URL serwisu Ollama    | http://ollama:11434 |
| `OLLAMA_MODEL` | Model do klasyfikacji | llama3.2:3b         |

**Dostępne modele:**

- `llama3.2:1b` - Najszybszy, niska dokładność (1GB RAM)
- `llama3.2:3b` - **Domyślny** - OK dokładność (2GB RAM)
- `llama3.2:7b` - **Zalecany** - dobra dokładność (4GB RAM)
- `mistral` - Najlepszy - wysoka dokładność (4GB RAM)

### Pliki

| Zmienna              | Opis                        | Domyślna wartość      |
| -------------------- | --------------------------- | --------------------- |
| `MAX_FILE_SIZE`      | Maks. rozmiar pliku (bajty) | 10485760 (10MB)       |
| `ALLOWED_EXTENSIONS` | Dozwolone rozszerzenia      | pdf,png,jpg,jpeg,tiff |
| `UPLOAD_DIR`         | Katalog uploadów            | /app/data/uploads     |
| `PROCESSED_DIR`      | Katalog przetworzonych      | /app/data/processed   |

## Deployment produkcyjny

### Quick start (serwer produkcyjny)

```bash
# 1. Sklonuj projekt
git clone https://github.com/marioabc/document_classify.git
cd document_classify

# 2. Konfiguracja
cp .env.example .env
nano .env  # ZMIEŃ hasła i DEBUG=False

# 3. Uruchom
docker-compose up -d --build

# 4. Sprawdź
curl http://localhost:8000/health
```

### Szczegółowa instrukcja

Zobacz **`DEPLOYMENT.md`** - pełna instrukcja deploymentu z:

- Konfiguracją Nginx + SSL
- Backupami bazy danych
- Monitoringiem i logami
- Skalowaniem i wydajnością
- Bezpieczeństwem

Zobacz **`DEPLOYMENT_CHECKLIST.md`** - szybki checklist krok po kroku

### Automatyczny deployment z GitHub

```bash
# Na serwerze produkcyjnym:
cd document_classify
git pull
docker-compose down
docker-compose up -d --build
```

## Rozszerzenia (opcjonalne)

### 1. Autentykacja API Key

Dodaj weryfikację API Key w `app/api/endpoints.py`:

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY = "twoj-sekretny-klucz"
api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
```

### 2. Rate limiting

Użyj `slowapi` do limitowania requestów:

```bash
pip install slowapi
```

### 3. Monitoring i metryki

Dodaj Prometheus + Grafana do monitorowania:

- Czas przetwarzania dokumentów
- Liczba requestów
- Użycie pamięci/CPU
- Dokładność klasyfikacji

### 4. Webhooks niestandardowe

Dostosuj URL callbacku w `app/api/endpoints.py:239`:

```python
callback_url = f"https://twoja-domena.com/api/callback/{element_id}"
```

## Technologie

- **FastAPI** - framework web
- **EasyOCR** - ekstrakcja tekstu (OCR)
- **Ollama** - lokalne modele LLM
- **PostgreSQL** - baza danych
- **Redis** - cache i kolejki
- **Docker** - konteneryzacja
- **Uvicorn** - serwer ASGI

## Dalszy rozwój

Planowane funkcjonalności:

- [ ] Wsparcie dla dokumentów PDF (wielostronicowych)
- [ ] Dashboard do monitorowania klasyfikacji
- [ ] API do fine-tuningu modelu LLM
- [ ] Eksport wyników do CSV/Excel
- [ ] Integracja z systemami EMR/EHR

## Licencja

MIT License

## Wsparcie

- **Dokumentacja**: Zobacz pliki `*.md` w projekcie
- **Issues**: https://github.com/marioabc/document_classify/issues
- **Deployment**: Zobacz `DEPLOYMENT.md`
- **LLM Classifier**: Zobacz `LLM_CLASSIFIER_README.md`

## Autorzy

Projekt stworzony dla potrzeb klasyfikacji dokumentów medycznych.
