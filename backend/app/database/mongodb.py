from motor.motor_asyncio import AsyncIOMotorClient
from app.config import MONGODB_URL, MONGODB_DB_NAME

client = None
db = None


async def connect_db():
    global client, db
    try:
        # Append tlsInsecure to URL if not present
        url = MONGODB_URL
        if "tlsInsecure=true" not in url and "tlsAllowInvalidCertificates=true" not in url:
            sep = "&" if "?" in url else "?"
            url += sep + "tlsInsecure=true"

        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        client = AsyncIOMotorClient(
            url,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
        )
        db = client[MONGODB_DB_NAME]
        await db.command("ping")
        print("Connected to MongoDB")
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
