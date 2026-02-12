# Finance Dashboard - Backend

FastAPI-basiertes Backend für das Finance Dashboard.

## Tech-Stack

- **Python 3.12+**
- **FastAPI** - Web Framework
- **SQLAlchemy (async)** - ORM
- **PostgreSQL** - Datenbank
- **Pydantic** - Datenvalidierung

## Projektstruktur

```
FinanceDashboardBackend/
├── app/
│   ├── main.py              # FastAPI App-Einstiegspunkt
│   ├── core/                # Konfiguration, Datenbank
│   ├── models/              # SQLAlchemy Models
│   ├── schemas/             # Pydantic Schemas
│   ├── crud/                # CRUD-Operationen
│   └── api/                 # API-Endpunkte
├── requirements.txt
└── .env.example
```

## Installation

```bash
# Virtual Environment erstellen
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dependencies installieren
pip install -r requirements.txt

# .env Datei erstellen
cp .env.example .env
# DATABASE_URL in .env anpassen

# Datenbank initialisieren
python -m app.core.init_db

# Server starten
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Dokumentation

- **API-Dokumentation:** http://localhost:8000/docs
- **Hauptdokumentation:** [FinanceDashboard](https://github.com/fnnbl/FinanceDashboard)
