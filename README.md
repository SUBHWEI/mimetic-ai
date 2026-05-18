# Mimetic AI

Sistema conversacional de apoyo al diagnóstico médico con autenticación por roles, registro de pacientes, login social y verificación por email.

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
| `admin` | Panel de administración, crear médicos |
| `medico` | Chat de diagnóstico, historias clínicas |
| `paciente` | Portal del paciente (próximamente) |

## Inicio rápido

```bash
# Backend (local)
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Frontend
cd frontend
npm install
npx vite --host 0.0.0.0 --port 5173
```

Variables de entorno requeridas (ver `start_backend.ps1`):
- `MONGODB_URL` — conexión a MongoDB Atlas
- `SMTP_USER` / `SMTP_PASSWORD` — credenciales Gmail SMTP
- `GOOGLE_CLIENT_ID` — OAuth de Google Login
- `FACEBOOK_APP_ID` / `FACEBOOK_APP_SECRET` — OAuth de Facebook Login
- `GMAIL_API_CLIENT_ID` / `GMAIL_API_CLIENT_SECRET` / `GMAIL_API_REFRESH_TOKEN` — Gmail API (HTTPS)

## API — Autenticación

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/auth/register` | Registro de paciente con datos personales |
| POST | `/api/auth/verify-email` | Verificar correo con código de 6 dígitos |
| POST | `/api/auth/login` | Inicio de sesión |
| POST | `/api/auth/social-login` | Login/registro con Google o Facebook |
| POST | `/api/auth/social-register` | Confirmar registro social con datos editados |
| POST | `/api/auth/create-user` | Crear usuario (admin) — rol: admin/medico |
| GET | `/api/auth/me` | Perfil del usuario autenticado |

### Campos del registro de paciente

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `email` | string | Correo electrónico (único) |
| `password` | string | Contraseña |
| `first_name` | string | Nombres |
| `last_name` | string | Apellidos |
| `document_type` | string | CC / CE / TI / Pasaporte / Otro |
| `document_number` | string | Número de documento (único) |
| `birth_date` | string | Fecha de nacimiento (YYYY-MM-DD) |
| `phone` | string | Teléfono de contacto |
| `country` | string | País |
| `department` | string | Departamento |
| `city` | string | Ciudad |

## API — Diagnóstico

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

## Despliegue

- **Frontend**: Vercel (`mimetic-ai.vercel.app`)
- **Backend**: Render Web Service (`mimetic-ai-api.onrender.com`)
- **Base de datos**: MongoDB Atlas

Configurar `VITE_API_URL` en Vercel apuntando al backend de Render.
