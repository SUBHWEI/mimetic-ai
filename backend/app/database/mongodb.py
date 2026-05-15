import ssl
from urllib.parse import urlparse, urlunparse
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import MONGODB_URL, MONGODB_DB_NAME

client = None
db = None

# Force TLS 1.2 globally
ssl._create_default_https_context = lambda: ssl._create_unverified_context(
    protocol=ssl.PROTOCOL_TLSv1_2
)


async def connect_db():
    global client, db
    try:
        client = AsyncIOMotorClient(
            MONGODB_URL,
            tls=True,
            tlsAllowInvalidCertificates=True,
            tlsAllowInvalidHostnames=True,
            serverSelectionTimeoutMS=20000,
            connectTimeoutMS=20000,
        )
        db = client[MONGODB_DB_NAME]
        await db.command("ping")
        print("Connected to MongoDB")
    except Exception as e:
        print("WARNING: Could not connect to MongoDB:", e)
        client = None
        db = None


async def close_db():
    global client
    if client:
        client.close()
        print("Disconnected from MongoDB")


def get_db():
    return db
