import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.mongodb import connect_db, close_db, get_db
from app.config import CORS_ORIGINS
from app.routes import diagnosis, knowledge, converse, patient, report, auth, clinical_history, hospitals

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


async def auto_seed():
    db = get_db()
    if db is None:
        return
    from seed_data import symptoms, diseases, treatments
    from seed_data import _upsert_many

    print("Synchronizing knowledge base (idempotent upsert)...")
    n_s = await _upsert_many(db.symptoms, symptoms, "name")
    n_d = await _upsert_many(db.diseases, diseases, "name")
    n_t = await _upsert_many(db.treatments, treatments, "disease_name")
    print(f"Knowledge base synced: {n_s} symptoms, {n_d} diseases, {n_t} treatments")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    await auto_seed()
    yield
    await close_db()


app = FastAPI(title="MIMETIC - Medical Expert System", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(diagnosis.router, prefix="/api", tags=["Diagnosis"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge Base"])
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(converse.router, prefix="/api", tags=["Conversation"])
app.include_router(patient.router, prefix="/api", tags=["Patient"])
app.include_router(report.router, prefix="/api", tags=["Report"])
app.include_router(clinical_history.router, prefix="/api", tags=["Clinical History"])
app.include_router(hospitals.router, prefix="/api", tags=["Hospitals"])


@app.get("/health")
async def health():
    from app.database.mongodb import get_db
    db_ok = get_db() is not None
    return {"status": "ok" if db_ok else "degraded", "service": "MIMETIC", "database": "connected" if db_ok else "disconnected"}
