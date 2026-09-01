from motor.motor_asyncio import AsyncIOMotorClient
from app.config import MONGODB_URL, MONGODB_DB_NAME

client = None
db = None


def _build_index_specs():
    """(collection, keys, options) para crear/garantizar índices de forma idempotente."""
    return [
        # Identidad y autenticación
        ("users", [("email", 1)], {"unique": True, "name": "users_email_unique"}),
        ("users", [("document_number", 1)], {"name": "users_document_number"}),
        # Historia clínica y sesiones
        ("clinical_histories", [("document_number", 1)], {"unique": True, "name": "clinical_histories_document_number_unique"}),
        ("sessions", [("document_number", 1), ("date", -1)], {"name": "sessions_document_date"}),
        ("sessions", [("doctor_id", 1)], {"name": "sessions_doctor_id"}),
        ("sessions", [("diagnoses.name", 1)], {"name": "sessions_diagnoses_name"}),
        # Hospitales
        ("hospitals", [("code", 1)], {"unique": True, "name": "hospitals_code_unique"}),
        # Catálogos de conocimiento
        ("symptoms", [("name", 1)], {"unique": True, "name": "symptoms_name_unique"}),
        ("symptoms", [("category", 1)], {"name": "symptoms_category"}),
        ("diseases", [("name", 1)], {"unique": True, "name": "diseases_name_unique"}),
        ("treatments", [("disease_name", 1)], {"unique": True, "name": "treatments_disease_name_unique"}),
        ("verification_codes", [("email", 1)], {"unique": True, "name": "verification_codes_email_unique"}),
    ]


async def create_indexes():
    """Crea los índices de la base de datos (idempotente). No rompe datos existentes."""
    try:
        for coll_name, keys, options in _build_index_specs():
            await db[coll_name].create_index(keys, **options)
        print("Indexes created/verified")
    except Exception as e:
        print("Warning: no se pudieron crear todos los índices:", type(e).__name__, e)


async def connect_db():
    global client, db
    try:
        # Uso TLS real: quitar parametros inseguros que desactivan la verificacion de certificados
        url = MONGODB_URL
        url = url.replace("tlsInsecure=true", "").replace("tlsAllowInvalidCertificates=true", "")
        url = url.replace("&&", "&").replace("?&", "?").rstrip("&?")

        client = AsyncIOMotorClient(
            url,
            tls=True,
            tlsAllowInvalidCertificates=False,
            tlsAllowInvalidHostnames=False,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
        )
        db = client[MONGODB_DB_NAME]
        await db.command("ping")
        print("Connected to MongoDB")
        await create_indexes()
    except Exception as e:
        print("=" * 60)
        print("MongoDB connection failed:", type(e).__name__)
        print("Error:", e)
        print("URL schema:", url.split("://")[0] if "://" in url else "unknown")
        print("=" * 60)
        client = None
        db = None


async def close_db():
    global client
    if client:
        client.close()
        print("Disconnected from MongoDB")


def get_db():
    return db
