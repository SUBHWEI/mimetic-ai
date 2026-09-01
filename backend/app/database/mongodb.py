from motor.motor_asyncio import AsyncIOMotorClient
from app.config import MONGODB_URL, MONGODB_DB_NAME

client = None
db = None


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
        await ensure_indexes(db)
        print("Connected to MongoDB")
    except Exception as e:
        print("=" * 60)
        print("MongoDB connection failed:", type(e).__name__)
        print("Error:", e)
        print("URL schema:", url.split("://")[0] if "://" in url else "unknown")
        print("=" * 60)
        client = None
        db = None


async def ensure_indexes(db):
    """Create unique indexes on critical collections to prevent duplicates."""
    try:
        await db.users.create_index(
            [("email", 1)],
            unique=True,
            name="uniq_users_email",
        )
        await db.users.create_index(
            [("document_number", 1)],
            unique=True,
            sparse=True,
            name="uniq_users_document_number",
        )
        await db.clinical_histories.create_index(
            [("document_number", 1)],
            unique=True,
            name="uniq_clinical_histories_document_number",
        )
        await db.hospitals.create_index(
            [("code", 1)],
            unique=True,
            name="uniq_hospitals_code",
        )
        print("MongoDB unique indexes ensured")
    except Exception as e:
        print("Error creando indices:", type(e).__name__, e)
        raise


async def close_db():
    global client
    if client:
        client.close()
        print("Disconnected from MongoDB")


def get_db():
    return db
