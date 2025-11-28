# Klasyfikator LLM - Dokumentacja

## Zmiany w systemie klasyfikacji

System klasyfikacji dokumentów został rozbudowany o **inteligentny klasyfikator oparty na lokalnym modelu LLM (Ollama)**.

### Architektura

1. **Główny klasyfikator** (`classifier_service.py`):
   - Najpierw próbuje użyć LLM klasyfikatora
   - Jeśli LLM nie jest dostępny lub ma niską pewność (<0.5), używa klasyfikatora opartego na regułach

2. **LLM Klasyfikator** (`llm_classifier_service.py`):
   - Używa lokalnego modelu Ollama (domyślnie `llama3.2:3b`)
   - Analizuje kontekst dokumentu, nie tylko słowa kluczowe
   - Zwraca typ dokumentu z poziomem pewności i uzasadnieniem

3. **Klasyfikator oparty na regułach** (fallback):
   - Oryginalny system oparty na słowach kluczowych
   - Używany gdy LLM nie jest dostępny

### Nowe komponenty

#### 1. Docker Compose
- Dodano serwis `ollama` - uruchamia lokalny serwer Ollama
- Dodano serwis `ollama-init` - automatycznie pobiera model przy pierwszym uruchomieniu

#### 2. Konfiguracja (config.py)
```python
OLLAMA_URL: str = "http://ollama:11434"  # URL serwisu Ollama w docker-compose
OLLAMA_MODEL: str = "llama3.2:3b"        # Nazwa modelu do użycia
```

#### 3. Zależności (requirements.txt)
- Dodano `requests==2.31.0` do komunikacji z API Ollama

## Uruchomienie

### 1. Docker Compose (produkcja)

```bash
# Uruchom wszystkie serwisy (w tym Ollama)
docker-compose up -d

# Model zostanie automatycznie pobrany przez serwis ollama-init
# Sprawdź logi inicjalizacji:
docker-compose logs ollama-init

# Sprawdź czy model jest dostępny:
docker-compose exec ollama ollama list
```

### 2. Lokalne testowanie

```bash
# 1. Uruchom Ollama lokalnie (jeśli nie masz w Docker)
ollama pull llama3.2:3b

# 2. Ustaw zmienną środowiskową
export OLLAMA_URL=http://localhost:11434

# 3. Uruchom test
source venv/bin/activate
python test_ocr.py
```

## Przykład działania

### Przed (klasyfikator oparty na regułach)
```
Text: "ZAŚWIADCZENIE O SZCZEPIENIU PRZECIW WZW TYPU B"
Result: ZASWIADCZENIE_INTERNISTA (confidence: 0.30)
Keywords: ['zaświadczenie']
```

**Problem**: Znajduje tylko słowo "zaświadczenie" i przypisuje do złego typu.

### Po (klasyfikator LLM)
```
Text: "ZAŚWIADCZENIE O SZCZEPIENIU PRZECIW WZW TYPU B"
Result: SZCZEPIENIE_WZW (confidence: 0.95)
Reasoning: "Dokument zawiera informacje o szczepieniu przeciw WZW typu B"
```

**Rozwiązanie**: LLM rozumie kontekst i prawidłowo klasyfikuje jako szczepienie.

## Zalety nowego podejścia

1. **Dokładność**: LLM rozumie kontekst, nie tylko słowa kluczowe
2. **Tolerancja błędów OCR**: LLM radzi sobie z błędami w rozpoznaniu tekstu
3. **Lokalność**: Model działa lokalnie, bez wysyłania danych do cloud
4. **Koszt**: Brak kosztów API - model działa na własnej infrastrukturze
5. **Fallback**: System automatycznie wraca do reguł jeśli LLM nie jest dostępny

## Konfiguracja modelu

Możesz zmienić model Ollama w `.env` lub `docker-compose.yml`:

```yaml
environment:
  - OLLAMA_MODEL=llama3.2:3b  # Mały, szybki model (2GB RAM)
  # - OLLAMA_MODEL=mistral     # Większy, dokładniejszy (4GB RAM)
  # - OLLAMA_MODEL=llama3.2:1b # Najmniejszy model (1GB RAM)
```

## Dostępne modele

**UWAGA**: Model `llama3.2:3b` może mieć problemy z dokładnością klasyfikacji dla niektórych dokumentów. Dla lepszych wyników zalecamy większy model.

- `llama3.2:1b` - Najmniejszy (1GB RAM), najszybszy - **NIE zalecany** (niska dokładność)
- `llama3.2:3b` - Domyślny - podstawowa klasyfikacja (2GB RAM) - **może mieć błędy**
- `mistral` - **ZALECANY** - Większy, dokładniejszy (4GB RAM)
- `llama3.2:7b` - **ZALECANY** - Najlepszy balans dokładności (4GB RAM)
- `phi3` - Mały i szybki, alternatywa dla llama3.2:3b (2GB RAM)

### Zmiana modelu

Aby zmienić model na dokładniejszy:

```bash
# W docker-compose.yml zmień:
environment:
  - OLLAMA_MODEL=mistral  # lub llama3.2:7b

# Następnie:
docker-compose down
docker-compose up -d

# Model zostanie automatycznie pobrany przez ollama-init
```

## Rozwiązywanie problemów

### LLM nie działa
```bash
# Sprawdź czy Ollama jest uruchomiona
docker-compose ps ollama

# Sprawdź logi
docker-compose logs ollama

# Sprawdź dostępne modele
docker-compose exec ollama ollama list

# Ręcznie pobierz model
docker-compose exec ollama ollama pull llama3.2:3b
```

### LLM jest wolny
- Zmniejsz model na `llama3.2:1b` lub `phi3`
- Użyj GPU jeśli dostępne (wymaga konfiguracji NVIDIA runtime)

### Spadek pewności
- Jeśli LLM zwraca pewność <0.5, system automatycznie użyje klasyfikatora opartego na regułach
- Możesz dostosować próg w `classifier_service.py` (linia 95)

## Monitorowanie

```bash
# Sprawdź logi klasyfikacji
docker-compose logs -f api | grep "Classification"

# Przykładowy output:
# LLM Classification: DocumentType.SZCZEPIENIE_WZW (confidence: 0.95)
# Rule-based classification: DocumentType.ZASWIADCZENIE_INTERNISTA (confidence: 0.30)
```
