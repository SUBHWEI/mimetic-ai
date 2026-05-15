from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.mongodb import connect_db, close_db, get_db
from app.routes import diagnosis, knowledge, converse, patient, report


async def auto_seed():
    db = get_db()
    if db is None:
        return
    existing = await db.diseases.count_documents({})
    if existing > 0:
        print("Database already seeded")
        return
    print("Seeding database...")
    from seed_data import symptoms, diseases, treatments
    if symptoms:
        await db.symptoms.insert_many(symptoms)
        print(f"  Inserted {len(symptoms)} symptoms")
    if diseases:
        await db.diseases.insert_many(diseases)
        print(f"  Inserted {len(diseases)} diseases")
    if treatments:
        await db.treatments.insert_many(treatments)
        print(f"  Inserted {len(treatments)} treatments")
    print("Seeding complete")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    await auto_seed()
    yield
    await close_db()


app = FastAPI(title="Mimetic AI - Medical Expert System", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(diagnosis.router, prefix="/api", tags=["Diagnosis"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge Base"])
app.include_router(converse.router, prefix="/api", tags=["Conversation"])
app.include_router(patient.router, prefix="/api", tags=["Patient"])
app.include_router(report.router, prefix="/api", tags=["Report"])


@app.get("/health")
async def health():
    from app.database.mongodb import get_db
    db_ok = get_db() is not None
    return {"status": "ok" if db_ok else "degraded", "service": "Mimetic AI", "database": "connected" if db_ok else "disconnected"}
