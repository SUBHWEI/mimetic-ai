from motor.motor_asyncio import AsyncIOMotorClient
from app.config import MONGODB_URL, MONGODB_DB_NAME

client = None
db = None


async def connect_db():
    global client, db
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[MONGODB_DB_NAME]
        await db.command("ping")
        print("Connected to MongoDB at", MONGODB_URL[:30] + "...")
    except Exception as e:
        print("WARNING: Could not connect to MongoDB:", e)
        print("App will start, but DB features won't work until connection is established.")
        client = None
        db = None


async def close_db():
    global client
    if client:
        client.close()
        print("Disconnected from MongoDB")


def get_db():
    return db
