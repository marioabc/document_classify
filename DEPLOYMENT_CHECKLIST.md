# Deployment Checklist - Quick Start

## Przed deploymentem

- [ ] Kod jest w repozytorium Git
- [ ] Wszystkie zmiany są scommitowane
- [ ] `.dockerignore` istnieje
- [ ] `.env.example` jest aktualny
- [ ] Przetestowane lokalnie: `docker-compose up --build`

## Na serwerze produkcyjnym

### Instalacja (tylko raz)

```bash
# 1. Zainstaluj Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# WYLOGUJ SIĘ I ZALOGUJ PONOWNIE

# 2. Zainstaluj Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin -y

# 3. Zweryfikuj instalację
docker --version
docker compose version
```

### Deployment aplikacji

```bash
# 1. Sklonuj projekt
git clone https://github.com/TWOJE-REPO/klasyfikacja_dokumentow.git
cd klasyfikacja_dokumentow

# 2. Konfiguracja
cp .env.example .env
nano .env  # ZMIEŃ HASŁA I DEBUG=False

# 3. Utwórz katalogi
mkdir -p data/uploads data/processed

# 4. Uruchom
docker-compose up -d --build

# 5. Sprawdź status
docker-compose ps
docker-compose logs -f

# 6. Test API
curl http://localhost:8000/health
```

### Opcjonalne: Nginx + SSL

```bash
# 1. Zainstaluj Nginx
sudo apt-get install nginx certbot python3-certbot-nginx -y

# 2. Stwórz config
sudo nano /etc/nginx/sites-available/medical-api

# Wklej:
server {
    listen 80;
    server_name TWOJA-DOMENA.com;
    client_max_body_size 20M;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300;
    }
}

# 3. Aktywuj
sudo ln -s /etc/nginx/sites-available/medical-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 4. SSL
sudo certbot --nginx -d TWOJA-DOMENA.com

# 5. Firewall
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## Codzienne operacje

### Aktualizacja

```bash
cd klasyfikacja_dokumentow
docker-compose down
git pull
docker-compose up -d --build
```

### Sprawdzenie statusu

```bash
docker-compose ps
docker-compose logs --tail=50 -f
```

### Restart

```bash
docker-compose restart
# lub tylko API:
docker-compose restart api
```

### Backup bazy

```bash
docker-compose exec postgres pg_dump -U medical_user medical_docs > backup_$(date +%Y%m%d).sql
```

## Ważne URLs (po uruchomieniu)

- API: http://localhost:8000
- Health check: http://localhost:8000/health
- Dokumentacja API: http://localhost:8000/docs
- Ollama: http://localhost:11434

## W razie problemów

```bash
# Sprawdź logi
docker-compose logs api
docker-compose logs ollama

# Sprawdź zasoby
docker stats

# Sprawdź miejsce
df -h
docker system df

# Wyczyść
docker system prune -a

# Przebuduj wszystko od nowa
docker-compose down -v
docker-compose up -d --build
```

## Kontakty alarmowe

- Dokumentacja: Zobacz DEPLOYMENT.md
- Logi: `docker-compose logs -f api`
- Monitoring: `docker stats`
