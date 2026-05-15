# Mimetic AI

Sistema conversacional de apoyo al diagnóstico médico con inteligencia artificial. Permite al doctor registrar datos del paciente, describir síntomas mediante lenguaje natural, obtener diagnósticos diferenciales, revisar tratamientos y generar una historia clínica profesional.

## Stack

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.11+ / FastAPI (Motor MongoDB async) |
| Frontend | React + Vite + TypeScript |
| Base de datos | MongoDB |
| Contenedor BD | Docker |

## Arquitectura

```
┌─────────────┐     ┌──────────────┐     ┌──────────┐
│  Frontend   │────▶│   Backend    │────▶│ MongoDB  │
│  React/Vite │     │  FastAPI     │     │ (Docker) │
│  :5173      │◀────│  :8001       │     │ :27017   │
└─────────────┘     └──────────────┘     └──────────┘
```

**Módulos del backend:**
- `routes/converse.py` — endpoint conversacional principal
- `routes/patient.py` — registro de datos del paciente
- `routes/report.py` — generación de historia clínica
- `routes/diagnosis.py` — diagnóstico y tratamiento directos
- `routes/knowledge.py` — consulta de base de conocimiento
- `expert_system/normalizer.py` — normalización de síntomas en lenguaje natural
- `expert_system/engine.py` — motor de diagnóstico por coincidencia de síntomas
- `expert_system/conversation.py` — generación de preguntas de seguimiento

## Requisitos locales

- Python 3.11+
- Node.js 18+
- Docker Desktop (para MongoDB)

## Inicio rápido

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd mimetic-ai

# 2. Iniciar MongoDB
docker run -d -p 27017:27017 --name mongodb mongo:7

# 3. Backend
cd backend
python -m venv .venv
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
python seed_data.py        # Poblar base de conocimiento
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# 4. Frontend
cd frontend
npm install
npx vite --host 0.0.0.0 --port 5173
```

Abrir http://localhost:5173

## Endpoints de la API

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/converse` | Chat conversacional con el asistente |
| POST | `/api/patient` | Registrar datos del paciente |
| POST | `/api/report` | Generar historia clínica completa |
| POST | `/api/diagnose` | Diagnóstico directo por síntomas |
| POST | `/api/treatment` | Obtener tratamiento por enfermedad |
| POST | `/api/learn` | Aprender nuevo sinónimo de síntoma |
| GET | `/api/knowledge/diseases` | Listar enfermedades |
| GET | `/api/knowledge/symptoms` | Listar síntomas |
| GET | `/api/knowledge/treatments` | Listar tratamientos |
| GET | `/health` | Estado del servicio |

## Despliegue

### Backend → Render

1. Crear un servicio **Web Service** en [Render](https://render.com)
2. Conectar el repositorio
3. Configurar:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Agregar variable de entorno:
   - `MONGODB_URL` → URL de conexión a MongoDB (usar [MongoDB Atlas](https://www.mongodb.com/atlas) o [Render Managed MongoDB](https://render.com/docs/mongodb))
5. La URL del backend será `https://tu-app.onrender.com`

### Frontend → Vercel

1. Instalar Vercel CLI: `npm i -g vercel`
2. En la raíz del proyecto:
   ```bash
   cd frontend
   vercel
   ```
3. O conectar el repositorio en [Vercel](https://vercel.com)
4. Configurar:
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
5. Agregar variable de entorno:
   - `VITE_API_URL` → URL del backend en Render

## Licencia

Proyecto académico / interno.
