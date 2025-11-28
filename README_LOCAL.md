# Uruchomienie lokalne (Development Mode)

Ten przewodnik pokazuje jak uruchomić aplikację Python lokalnie, z bazami danych w Docker.

## Zalety uruchomienia lokalnego

✅ **Szybszy development** - nie trzeba przebudowywać obrazu Docker przy każdej zmianie
✅ **Łatwiejsze debugowanie** - bezpośredni dostęp do kodu i logów
✅ **Hot reload** - automatyczne przeładowanie przy zmianach w kodzie
✅ **IDE integration** - pełne wsparcie dla debuggera i intellisense

## Wymagania

- Python 3.11+
- Docker i Docker Compose (tylko dla baz danych)
- pip i venv

## Metoda 1: Automatyczne uruchomienie (zalecane)

### Uruchom wszystko jednym skryptem:

```bash
./run_local.sh
```

Skrypt automatycznie:
1. Uruchomi PostgreSQL i Redis w Docker
2. Utworzy virtual environment (jeśli nie istnieje)
3. Zainstaluje zależności
4. Uruchomi aplikację z hot reload

### Zatrzymanie:

```bash
# Zatrzymaj aplikację: Ctrl+C

# Zatrzymaj bazy danych:
docker-compose -f docker-compose.dev.yml down
```

---

## Metoda 2: Manualne uruchomienie (krok po kroku)

### 1. Uruchom bazy danych w Docker

```bash
# Kopiuj konfigurację lokalną
cp .env.local .env

# Uruchom PostgreSQL i Redis
docker-compose -f docker-compose.dev.yml up -d

# Sprawdź status
docker-compose -f docker-compose.dev.yml ps
```

### 2. Utwórz i aktywuj virtual environment

```bash
# Utwórz venv
python3 -m venv venv

# Aktywuj venv (macOS/Linux)
source venv/bin/activate

# Lub aktywuj venv (Windows)
# venv\Scripts\activate
```

### 3. Zainstaluj zależności

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Uruchom aplikację

```bash
# Z hot reload (development)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Bez hot reload (production-like)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 5. Sprawdź działanie

```bash
# Health check
curl http://localhost:8000/health

# Dokumentacja API
open http://localhost:8000/docs
```

---

## Workflow developmentu

### Typowy cykl pracy:

1. **Start** - uruchom bazy danych i aplikację:
   ```bash
   ./run_local.sh
   ```

2. **Edytuj kod** - zmiany są automatycznie wykrywane (hot reload)

3. **Testuj** - użyj Swagger UI (http://localhost:8000/docs) lub curl

4. **Debuguj** - użyj debuggera w IDE (VS Code, PyCharm)

5. **Stop** - Ctrl+C, potem:
   ```bash
   docker-compose -f docker-compose.dev.yml down
   ```

---

## Konfiguracja

### Plik .env.local

Lokalna konfiguracja znajduje się w `.env.local`:

```env
# Ważne różnice dla lokalnego uruchomienia:
POSTGRES_HOST=localhost    # nie "postgres"!
REDIS_HOST=localhost       # nie "redis"!
UPLOAD_DIR=./data/uploads  # ścieżka względna
```

### Porty

Bazy danych są wystawione na localhost:

- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`
- **API**: `localhost:8000`

---

## Debugowanie w VS Code

### 1. Utwórz `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI Local",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
      ],
      "jinja": true,
      "justMyCode": true,
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      },
      "envFile": "${workspaceFolder}/.env.local"
    }
  ]
}
```

### 2. Uruchom bazy danych:

```bash
docker-compose -f docker-compose.dev.yml up -d
```

### 3. Uruchom debugger (F5)

---

## Testowanie

### Uruchom testy:

```bash
# Aktywuj venv
source venv/bin/activate

# Wszystkie testy
pytest

# Z pokryciem kodu
pytest --cov=app tests/

# Tylko testy API
pytest tests/test_api.py -v

# Tylko testy klasyfikatora
pytest tests/test_classifier.py -v
```

---

## Połączenie z bazą danych

### Połącz się z PostgreSQL:

```bash
# Przez docker exec
docker exec -it medical-doc-db-dev psql -U medical_user -d medical_docs

# Lub bezpośrednio (jeśli masz psql)
psql -h localhost -U medical_user -d medical_docs
```

### Popularne komendy SQL:

```sql
-- Lista tabel
\dt

-- Pokaż wszystkie dokumenty
SELECT * FROM documents;

-- Statystyki typów dokumentów
SELECT document_type, COUNT(*)
FROM documents
GROUP BY document_type;

-- Ostatnie 10 dokumentów
SELECT filename, document_type, confidence, upload_timestamp
FROM documents
ORDER BY upload_timestamp DESC
LIMIT 10;
```

---

## Zarządzanie bazami danych

### Reset bazy danych:

```bash
# Zatrzymaj i usuń wszystko
docker-compose -f docker-compose.dev.yml down -v

# Uruchom ponownie (czysta baza)
docker-compose -f docker-compose.dev.yml up -d
```

### Backup bazy danych:

```bash
# Backup
docker exec medical-doc-db-dev pg_dump -U medical_user medical_docs > backup.sql

# Restore
cat backup.sql | docker exec -i medical-doc-db-dev psql -U medical_user medical_docs
```

---

## Przełączanie między trybami

### Z lokalnego na Docker:

```bash
# Zatrzymaj lokalne
# Ctrl+C w terminalu z uvicorn

# Zatrzymaj bazy danych dev
docker-compose -f docker-compose.dev.yml down

# Uruchom pełny Docker
docker-compose up -d
```

### Z Docker na lokalne:

```bash
# Zatrzymaj Docker
docker-compose down

# Uruchom lokalne
./run_local.sh
```

---

## Troubleshooting

### Problem: "Port already in use"

```bash
# Sprawdź co używa portu 8000
lsof -i :8000

# Zabij proces
kill -9 <PID>
```

### Problem: "Could not connect to database"

```bash
# Sprawdź czy kontenery działają
docker-compose -f docker-compose.dev.yml ps

# Sprawdź logi
docker-compose -f docker-compose.dev.yml logs postgres

# Restart baz danych
docker-compose -f docker-compose.dev.yml restart
```

### Problem: "Module not found"

```bash
# Sprawdź czy venv jest aktywny
which python  # powinno pokazać ścieżkę z 'venv'

# Jeśli nie, aktywuj:
source venv/bin/activate

# Reinstaluj zależności
pip install -r requirements.txt
```

### Problem: EasyOCR nie pobiera modeli

```bash
# Pobierz modele ręcznie
python -c "import easyocr; reader = easyocr.Reader(['pl', 'en'], gpu=False)"
```

---

## Porównanie trybów

| Aspekt | Docker | Lokalne |
|--------|--------|---------|
| Szybkość startu | 🐢 Wolniejszy | ⚡ Szybszy |
| Hot reload | ❌ Wymaga rebuildu | ✅ Automatyczny |
| Debugowanie | 🔧 Trudniejsze | 🎯 Łatwe |
| Izolacja | ✅ Pełna | ⚠️ Zależności systemowe |
| Production-like | ✅ Tak | ❌ Nie |
| **Użycie** | **Testing, CI/CD** | **Development** |

---

## Zalecenia

- **Development**: Używaj uruchomienia lokalnego (`./run_local.sh`)
- **Testing**: Testuj zmiany w Docker przed commitem
- **Production**: Zawsze używaj Docker

---

## Przydatne komendy

```bash
# Status wszystkiego
docker-compose -f docker-compose.dev.yml ps
ps aux | grep uvicorn

# Logi baz danych
docker-compose -f docker-compose.dev.yml logs -f postgres
docker-compose -f docker-compose.dev.yml logs -f redis

# Restart tylko bazy danych
docker-compose -f docker-compose.dev.yml restart postgres

# Wyczyść wszystko
docker-compose -f docker-compose.dev.yml down -v
deactivate  # wyjdź z venv
rm -rf venv  # usuń venv
```
