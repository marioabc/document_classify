#!/bin/bash

# Skrypt do uruchamiania aplikacji lokalnie (bez Dockera dla Python)
# Bazy danych (PostgreSQL i Redis) są uruchamiane w Docker

set -e

echo "🚀 Uruchamianie Medical Document Classifier w trybie lokalnym..."

# Sprawdź czy .env.local istnieje
if [ ! -f .env.local ]; then
    echo "❌ Brak pliku .env.local! Kopiuję z .env.local.example..."
    cp .env.local .env.local
fi

# Kopiuj .env.local do .env (aplikacja czyta z .env)
cp .env.local .env

echo "✅ Konfiguracja załadowana z .env.local"

# Baza danych nie jest potrzebna - aplikacja tylko klasyfikuje dokumenty

# Sprawdź czy lokalne Ollama działa
if ! pgrep -f "ollama serve" > /dev/null; then
    echo "⚠️  Ollama nie jest uruchomione lokalnie!"
    echo "💡 Uruchom Ollama: ollama serve"
    echo "💡 Lub zainstaluj: brew install ollama"
else
    echo "✅ Ollama działa lokalnie (z GPU/Metal)"
fi

# Sprawdź czy virtual environment istnieje
if [ ! -d "venv" ]; then
    echo "📦 Tworzenie virtual environment..."
    python3.11 -m venv venv
    echo "✅ Virtual environment utworzony"
fi

# Aktywuj virtual environment
echo "🔧 Aktywowanie virtual environment..."
source venv/bin/activate

# Zainstaluj zależności
echo "📥 Instalowanie zależności..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Wszystko gotowe!"
echo ""
echo "🌐 Uruchamianie aplikacji na http://localhost:8000"
echo "📚 Dokumentacja API: http://localhost:8000/docs"
echo "🤖 Ollama (LLM, lokalne z GPU): http://localhost:11434"
echo ""
echo "💡 Aby zatrzymać aplikację: Ctrl+C"
echo "💡 Lista modeli Ollama: ollama list"
echo ""
echo "ℹ️  Bazy danych wyłączone - aplikacja tylko klasyfikuje"
echo ""

# Uruchom aplikację
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
