# Mimetic AI

Sistema conversacional de apoyo al diagnóstico médico. Permite al médico registrar datos del paciente, describir síntomas en lenguaje natural, obtener diagnósticos diferenciales, revisar tratamientos y generar una historia clínica profesional.

## Stack

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.11+ / FastAPI (Motor MongoDB async) |
| Frontend | React + Vite + TypeScript |
| Base de datos | MongoDB |

## Arquitectura

```
┌─────────────┐     ┌──────────────┐     ┌──────────┐
│  Frontend   │────▶│   Backend    │────▶│ MongoDB  │
│  React/Vite │     │  FastAPI     │     │          │
│  :5173      │◀────│  :8001       │     │ :27017   │
└─────────────┘     └──────────────┘     └──────────┘
```

## Inicio rápido

```bash
# MongoDB
docker run -d -p 27017:27017 --name mongodb mongo:7

# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python seed_data.py
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Frontend
cd frontend
npm install
npx vite --host 0.0.0.0 --port 5173
```

Abrir http://localhost:5173

## API

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/converse` | Chat conversacional |
| POST | `/api/patient` | Registrar datos del paciente |
| POST | `/api/report` | Generar historia clínica |
| POST | `/api/diagnose` | Diagnosticar por síntomas |
| POST | `/api/treatment` | Obtener tratamiento |
| POST | `/api/learn` | Enseñar nuevo sinónimo |
| GET | `/api/knowledge/diseases` | Enfermedades registradas |
| GET | `/api/knowledge/symptoms` | Síntomas registrados |
| GET | `/api/knowledge/treatments` | Tratamientos registrados |
| GET | `/health` | Estado del servicio |
