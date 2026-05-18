from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timedelta
import random
from jose import jwt
from passlib.context import CryptContext
from app.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_HOURS
from app.database.mongodb import get_db
from app.models.user import UserCreate, UserCreateByAdmin, UserLogin, UserOut, Token
from app.auth.dependencies import get_current_user
from app.email.sender import send_verification_code

router = APIRouter(prefix="/auth", tags=["Authentication"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def require_admin(current_user: UserOut = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate):
    db = get_db()

    existing = await db.users.find_one({"email": data.email})
    if existing:
        if existing.get("verified"):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        else:
            code = str(random.randint(100000, 999999))
            await db.verification_codes.update_one(
                {"email": data.email},
                {"$set": {"code": code, "expires_at": datetime.utcnow() + timedelta(minutes=10)}},
                upsert=True,
            )
            try:
                send_verification_code(data.email, code, data.name)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
            return {"message": "Verification code sent to email", "email": data.email}

    password_hash = pwd_context.hash(data.password)
    user_doc = {
        "email": data.email,
        "name": data.name,
        "password_hash": password_hash,
        "role": "paciente",
        "verified": False,
        "created_at": datetime.utcnow(),
    }
    result = await db.users.insert_one(user_doc)

    code = str(random.randint(100000, 999999))
    await db.verification_codes.update_one(
        {"email": data.email},
        {"$set": {"code": code, "expires_at": datetime.utcnow() + timedelta(minutes=10)}},
        upsert=True,
    )

    try:
        send_verification_code(data.email, code, data.name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

    return {"message": "Verification code sent to email", "email": data.email}


@router.post("/verify-email", response_model=Token)
async def verify_email(data: dict):
    db = get_db()
    email = data.get("email")
    code = data.get("code")

    if not email or not code:
        raise HTTPException(status_code=400, detail="Email and code required")

    stored = await db.verification_codes.find_one({"email": email})
    if not stored:
        raise HTTPException(status_code=400, detail="No verification code found. Register again.")

    if stored["code"] != code:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    if stored["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Verification code expired. Register again.")

    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    await db.users.update_one({"email": email}, {"$set": {"verified": True}})
    await db.verification_codes.delete_one({"email": email})

    user_id = str(user["_id"])
    access_token = create_access_token(user_id)

    return Token(
        access_token=access_token,
        user=UserOut(id=user_id, email=user["email"], name=user["name"], role=user["role"], created_at=user["created_at"]),
    )


@router.post("/create-user", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreateByAdmin, admin: UserOut = Depends(require_admin)):
    db = get_db()

    if data.role not in ("admin", "medico", "paciente"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role. Use: admin, medico, paciente")

    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    password_hash = pwd_context.hash(data.password)
    user_doc = {
        "email": data.email,
        "name": data.name,
        "password_hash": password_hash,
        "role": data.role,
        "verified": True,
        "created_at": datetime.utcnow(),
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)

    return UserOut(id=user_id, email=data.email, name=data.name, role=data.role, created_at=user_doc["created_at"])


@router.post("/login", response_model=Token)
async def login(data: UserLogin):
    db = get_db()

    user = await db.users.find_one({"email": data.email})
    if not user or not pwd_context.verify(data.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not user.get("verified", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified")

    user_id = str(user["_id"])
    access_token = create_access_token(user_id)

    return Token(
        access_token=access_token,
        user=UserOut(id=user_id, email=user["email"], name=user["name"], role=user["role"], created_at=user["created_at"]),
    )


@router.get("/me", response_model=UserOut)
async def get_me(current_user: UserOut = Depends(get_current_user)):
    return current_user
