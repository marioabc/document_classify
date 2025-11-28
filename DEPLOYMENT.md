# Instrukcja Deploymentu - Medical Document Classifier

## Wymagania serwera produkcyjnego

- Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- Docker 20.10+
- Docker Compose 2.0+
- Min. 4GB RAM (zalecane 8GB dla Ollama)
- Min. 20GB miejsca na dysku
- Git

## Opcja 1: Deployment przez Git (ZALECANE)

### 1. Przygotowanie serwera

```bash
# Zainstaluj Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Zainstaluj Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Zaloguj się ponownie aby zastosować grupę docker
```

### 2. Sklonuj repozytorium

```bash
# Sklonuj projekt
git clone https://github.com/twoje-repo/klasyfikacja_dokumentow.git
cd klasyfikacja_dokumentow
```

### 3. Konfiguracja środowiska

```bash
# Skopiuj przykładowy plik .env
cp .env.example .env

# Edytuj .env i ustaw produkcyjne wartości
nano .env
```

**WAŻNE zmiany w .env dla produkcji:**

```bash
# Zmień DEBUG na False
DEBUG=False

# Ustaw SILNE hasło do bazy danych
POSTGRES_PASSWORD=BARDZO_SILNE_HASLO_TUTAJ

# Opcjonalnie zmień model Ollama na dokładniejszy
OLLAMA_MODEL=llama3.2:7b  # lub mistral
```

### 4. Utwórz katalogi dla danych

```bash
mkdir -p data/uploads data/processed
```

### 5. Uruchom aplikację

```bash
# Build i uruchom wszystkie serwisy
docker-compose up -d --build

# Sprawdź logi
docker-compose logs -f

# Sprawdź status
docker-compose ps
```

### 6. Weryfikacja

```bash
# Sprawdź czy API działa
curl http://localhost:8000/health

# Sprawdź czy Ollama działa
curl http://localhost:11434/api/tags
```

### 7. Aktualizacje

```bash
# Zatrzymaj aplikację
docker-compose down

# Pobierz najnowszy kod
git pull

# Przebuduj i uruchom
docker-compose up -d --build
```

---

## Opcja 2: Deployment przez Docker Registry

### 1. Lokalnie - Build i Push

```bash
# Zaloguj się do Docker Hub (lub innego registry)
docker login

# Zbuduj obraz
docker build -f docker/Dockerfile.api -t twoja-nazwa/medical-doc-api:latest .

# Wypchnij do registry
docker push twoja-nazwa/medical-doc-api:latest
```

### 2. Na serwerze - Pull i Run

```bash
# Sklonuj tylko docker-compose.yml i .env
mkdir klasyfikacja_dokumentow && cd klasyfikacja_dokumentow

# Utwórz docker-compose.yml (zmodyfikowany)
# Zmień linię:
#   build:
#     context: .
#     dockerfile: docker/Dockerfile.api
# Na:
#   image: twoja-nazwa/medical-doc-api:latest

# Uruchom
docker-compose up -d
```

---

## Produkcyjne ustawienia

### 1. Nginx Reverse Proxy (ZALECANE)

Stwórz `/etc/nginx/sites-available/medical-doc-api`:

```nginx
server {
    listen 80;
    server_name twoja-domena.com;

    client_max_body_size 20M;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout dla długich requestów (OCR)
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/medical-doc-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2. SSL/HTTPS z Let's Encrypt

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d twoja-domena.com
```

### 3. Firewall

```bash
# Zezwól tylko na HTTP/HTTPS
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

---

## Monitorowanie i maintenance

### Logi

```bash
# Wszystkie logi
docker-compose logs -f

# Tylko API
docker-compose logs -f api

# Tylko Ollama
docker-compose logs -f ollama

# Ostatnie 100 linii
docker-compose logs --tail=100
```

### Backup bazy danych

```bash
# Backup
docker-compose exec postgres pg_dump -U medical_user medical_docs > backup_$(date +%Y%m%d).sql

# Restore
docker-compose exec -T postgres psql -U medical_user medical_docs < backup_20241128.sql
```

### Restart serwisów

```bash
# Restart całości
docker-compose restart

# Restart tylko API
docker-compose restart api

# Restart tylko Ollama
docker-compose restart ollama
```

### Czyszczenie

```bash
# Usuń nieużywane obrazy
docker image prune -a

# Usuń nieużywane volume'y
docker volume prune
```

---

## Troubleshooting

### Problem: Ollama nie pobiera modelu

```bash
# Ręcznie pobierz model
docker-compose exec ollama ollama pull llama3.2:3b

# Sprawdź dostępne modele
docker-compose exec ollama ollama list
```

### Problem: Brak miejsca na dysku

```bash
# Sprawdź użycie
df -h
docker system df

# Wyczyść
docker system prune -a --volumes
```

### Problem: API nie odpowiada

```bash
# Sprawdź logi
docker-compose logs api

# Sprawdź zasoby
docker stats

# Restart
docker-compose restart api
```

### Problem: Błędy OCR

```bash
# Sprawdź czy są zainstalowane zależności
docker-compose exec api python -c "import easyocr; print('OK')"

# Przebuduj obraz
docker-compose up -d --build api
```

---

## Bezpieczeństwo

1. **Zawsze zmień domyślne hasła** w `.env`
2. **Użyj HTTPS** w produkcji
3. **Regularnie aktualizuj** Docker obrazy: `docker-compose pull && docker-compose up -d`
4. **Ogranicz dostęp** do portów (tylko 80/443 przez firewall)
5. **Backup bazy danych** regularnie
6. **Monitoruj logi** pod kątem podejrzanych działań

---

## Koszty i wydajność

### Model Ollama

- `llama3.2:1b` - 1GB RAM, szybki, niska dokładność
- `llama3.2:3b` - 2GB RAM, średni, OK dokładność (domyślny)
- `llama3.2:7b` - 4GB RAM, wolniejszy, dobra dokładność (ZALECANY)
- `mistral` - 4GB RAM, wolniejszy, najlepsza dokładność

### Skalowanie

Dla większego ruchu użyj wielu workerów Uvicorn:
- W `docker/Dockerfile.api` zmień `--workers 4` na większą liczbę
- Zalecane: `2 × liczba_rdzeni_CPU`

---

## Kontakt i wsparcie

W razie problemów sprawdź:
- Logi: `docker-compose logs -f`
- GitHub Issues: https://github.com/twoje-repo/issues
- Dokumentacja Ollama: https://ollama.ai/docs
