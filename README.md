# Mimetic AI

Sistema conversacional de apoyo al diagnóstico médico. El médico registra al paciente, describe los síntomas y el sistema devuelve diagnósticos diferenciales con tratamientos y genera la historia clínica en PDF.

## Stack

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.11+ / FastAPI (Motor MongoDB async) |
| Frontend | React + Vite + TypeScript |
| Base de datos | MongoDB |
| Email | Gmail API (HTTPS) |
| Autenticación | JWT + Google OAuth + Facebook SDK |

## Arquitectura

```
┌─────────────┐     ┌──────────────┐     ┌──────────┐
│  Frontend   │────▶│   Backend    │────▶│ MongoDB  │
│  React/Vite │     │  FastAPI     │     │          │
│  Vercel     │◀────│  Render      │     │ Atlas    │
└─────────────┘     └──────────────┘     └──────────┘
```

## Roles

| Rol | Acceso |
|-----|--------|
| `admin` | Panel de administración, crear usuarios |
| `medico` | Chat de diagnóstico, historias clínicas |
| `paciente` | Consulta sus diagnósticos y tratamientos |

## Inicio rápido

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --port 8001 --reload

# Frontend
cd frontend
npm install
npx vite --port 5173
```

Variables de entorno (ver `start_backend.ps1`):
- `MONGODB_URL` — conexión a MongoDB Atlas
- `SMTP_USER` / `SMTP_PASSWORD` — credenciales Gmail SMTP
- `GOOGLE_CLIENT_ID` — OAuth de Google Login
- `FACEBOOK_APP_ID` / `FACEBOOK_APP_SECRET` — OAuth de Facebook Login
- `GMAIL_API_CLIENT_ID` / `GMAIL_API_CLIENT_SECRET` / `GMAIL_API_REFRESH_TOKEN` — Gmail API (HTTPS)

## Diagnóstico conversacional

El flujo principal es:

1. **Registro del paciente** — formulario con datos personales, antecedentes, signos vitales
2. **Chat de síntomas** — el médico describe los síntomas, el sistema hace preguntas para discriminar entre enfermedades
3. **Diagnóstico** — muestra hasta 3 enfermedades con nivel de confianza
4. **Tratamiento** — medicamentos recomendados con dosis, contraindicaciones, ajustes por peso/embarazo/alergias
5. **Reporte PDF** — historia clínica completa lista para imprimir

### Funcionalidades del motor de diagnóstico

- 50 enfermedades con síntomas y tratamientos (medicamentos, dosis, contraindicaciones)
- Interpreta lenguaje natural del médico (sinónimos, frases coloquiales)
- Preguntas discriminantes cuando hay varios diagnósticos posibles
- Auto-detección de síntomas desde signos vitales (fiebre > 37.5, taquipnea, PA alta, etc.)
- Ajuste de dosis pediátrico por peso (mg/kg) siguiendo guías colombianas
- Filtro de medicamentos por alergias, embarazo y comorbilidades
- Explicaciones en español sencillo para el paciente (`patient_summary`)

## API

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/auth/register` | Registro de paciente |
| POST | `/api/auth/login` | Inicio de sesión |
| POST | `/api/auth/create-user` | Crear usuario (admin) |
| GET | `/api/auth/me` | Perfil del usuario autenticado |
| POST | `/api/converse` | Chat conversacional de diagnóstico |
| POST | `/api/diagnose` | Diagnosticar por lista de síntomas |
| POST | `/api/report` | Generar historia clínica en PDF |
| POST | `/api/clinical-history` | Crear historia clínica del paciente |
| GET | `/api/clinical-history/search` | Buscar paciente por documento |
| POST | `/api/clinical-history/{doc}/sessions` | Crear sesión de consulta |
| GET | `/api/knowledge/diseases` | Enfermedades registradas |
| GET | `/api/knowledge/symptoms` | Síntomas registrados |
| GET | `/api/knowledge/treatments` | Tratamientos registrados |
| GET | `/health` | Estado del servicio |

## Despliegue

- **Frontend**: Vercel
- **Backend**: Render Web Service
- **Base de datos**: MongoDB Atlas

Configurar `VITE_API_URL` en Vercel apuntando al backend de Render.
