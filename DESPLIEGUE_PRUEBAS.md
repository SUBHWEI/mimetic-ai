# Despliegue de un ENTORNO DE PRUEBAS separado (Render + Vercel)

Esta guía te permite crear una copia del sistema **sin afectar el prototipo inicial**.
Se usa una **base de datos separada** (`mimetic_ai_dev`) y servicios **nuevos** en
Render (backend) y Vercel (frontend).

> **Importante:** esto NO modifica GitHub. Solo creas servicios nuevos en los paneles
> de Render y Vercel apuntando a la misma rama del repositorio (o a un fork).

---

## 1) Backend de pruebas → NUEVO servicio en Render

Crea un **nuevo** Web Service (no toques el que ya existe del prototipo).

1. En [dashboard.render.com](https://dashboard.render.com) → **New** → **Web Service**.
2. Conecta tu repositorio y selecciona la rama **`manuel_dev`** (o la rama con los
   cambios de pruebas) como rama de despliegue.
3. Configuración del servicio:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT` (o usa uvicorn)
4. En **Environment** pega todas las variables del archivo `backend/.env.production.example`.
   Punto clave: `MONGODB_DB_NAME=mimetic_ai_dev` → DB **separada** del prototipo.
5. **Deploy**. Te dará una URL tipo: `https://tu-backend-pruebas.onrender.com`

> Si no usas gunicorn, el Start Command puede ser:
> `uvicorn main:app --host 0.0.0.0 --port $PORT`

---

## 2) Frontend de pruebas → NUEVO proyecto en Vercel

Crea un **nuevo** proyecto (no toques el del prototipo).

1. En [vercel.com](https://vercel.com) → **Add New** → **Project**.
2. Conecta el repositorio y selecciona la misma rama de pruebas (`manuel_dev`).
3. **Root Directory**: `frontend`.
4. En **Environment Variables** agrega:

   | Variable | Valor |
   |----------|-------|
   | `VITE_API_URL` | `https://tu-backend-pruebas.onrender.com` (la URL del paso 1) |

5. **Deploy**. Te dará una URL tipo: `https://tu-frontend-pruebas.vercel.app`

> En producción por defecto el frontend usaba `https://mimetic-ai-api.onrender.com`
> (ver `frontend/src/config.ts`). Al definir `VITE_API_URL`, la copia de pruebas
> apunta a tu backend nuevo y NO al prototipo.

---

## 3) Verificación

- Abre `https://tu-backend-pruebas.onrender.com/health` → debe devolver `{"status":"ok"}`.
- Abre `https://tu-backend-pruebas.onrender.com/docs` → Swagger UI (probar la API de conocimiento:
  CRUD, `POST /api/knowledge/bulk`, `GET /api/knowledge/integrity`).
- Abre `https://tu-frontend-pruebas.vercel.app` → la app de pruebas.

---

## 4) Visualización local (opcional, sin desplegar)

Los scripts de inicio usan **puertos y DB separados** para que puedas probar todo en tu
máquina antes de desplegar:

```powershell
# Desde la raíz del proyecto
.\start_dev_full.ps1
```

- Backend local: `http://127.0.0.1:8002` (Swagger en `/docs`)
- Frontend local: `http://127.0.0.1:5174`
- Base de datos local: `mimetic_ai_dev` (separada)

Para probar los scripts de gestión y alimentación (en `backend/`):

```powershell
# Roles / cuentas de admin desde la terminal
python manage_admin.py create-admin --email admin@pruebas.com --name Admin --password "MiClave123"

# Generar conocimiento con IA (requiere GEMINI_API_KEY u OPENAI_API_KEY)
python ai_generate_knowledge.py --diseases "Dengue, Malaria" --dry-run

# Importar desde CSV / Excel / JSON
python import_from_excel.py --file datos.csv --type csv --dry-run
```

---

## Notas

- La rama `manuel_dev` contiene los cambios: índices en MongoDB, seed idempotente,
  API CRUD de conocimiento, script de IA, importación desde archivos y gestión de
  admin desde terminal.
- Nada de esto se ha desplegado ni modificado en el prototipo original.
