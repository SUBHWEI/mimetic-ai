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


def user_to_out(user: dict) -> UserOut:
    return UserOut(
        id=str(user["_id"]),
        email=user.get("email", ""),
        name=user.get("name", ""),
        role=user.get("role", "paciente"),
        first_name=user.get("first_name", ""),
        last_name=user.get("last_name", ""),
        document_type=user.get("document_type", ""),
        document_number=user.get("document_number", ""),
        birth_date=user.get("birth_date", ""),
        country=user.get("country", ""),
        department=user.get("department", ""),
        city=user.get("city", ""),
        phone=user.get("phone", ""),
        created_at=user.get("created_at", datetime.utcnow()),
    )


def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def require_admin(current_user: UserOut = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


@router.post("/test-email")
async def test_email(data: dict):
    email = data.get("email", "")
    if not email:
        raise HTTPException(status_code=400, detail="Email required")
    from app.email.sender import send_verification_code
    code = str(random.randint(100000, 999999))
    send_verification_code(email, code, "Test User")
    return {"message": "Email sent (check Render logs for errors)", "code_preview": code}


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate):
    db = get_db()

    existing = await db.users.find_one({"email": data.email})
    if existing:
        if existing.get("verified"):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        else:
            if data.document_number:
                doc_exists = await db.users.find_one({"document_number": data.document_number, "_id": {"$ne": existing["_id"]}})
                if doc_exists:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document number already registered")
            await db.users.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "name": data.name,
                    "first_name": data.first_name,
                    "last_name": data.last_name,
                    "document_type": data.document_type,
                    "document_number": data.document_number,
                    "birth_date": data.birth_date,
                    "country": data.country,
                    "department": data.department,
                    "city": data.city,
                    "phone": data.phone,
                    "password_hash": pwd_context.hash(data.password),
                }},
            )
            code = str(random.randint(100000, 999999))
            await db.verification_codes.update_one(
                {"email": data.email},
                {"$set": {"code": code, "expires_at": datetime.utcnow() + timedelta(minutes=10)}},
                upsert=True,
            )
            send_verification_code(data.email, code, data.name)
            return {"message": "Verification code sent to email", "email": data.email}

    if data.document_number:
        doc_exists = await db.users.find_one({"document_number": data.document_number})
        if doc_exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document number already registered")

    password_hash = pwd_context.hash(data.password)
    user_doc = {
        "email": data.email,
        "name": data.name,
        "password_hash": password_hash,
        "role": "paciente",
        "first_name": data.first_name,
        "last_name": data.last_name,
        "document_type": data.document_type,
        "document_number": data.document_number,
        "birth_date": data.birth_date,
        "country": data.country,
        "department": data.department,
        "city": data.city,
        "phone": data.phone,
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

    send_verification_code(data.email, code, data.name)
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

    return Token(access_token=access_token, user=user_to_out(user))


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
    user = await db.users.find_one({"_id": result.inserted_id})

    return user_to_out(user)


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

    return Token(access_token=access_token, user=user_to_out(user))


async def verify_social_token(provider: str, token: str, email: str = "", name: str = "") -> dict:
    if provider == "google":
        import httpx

        async with httpx.AsyncClient() as client:
            me_res = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                params={"access_token": token},
            )
            if me_res.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid Google token")
            me_data = me_res.json()
            return {"email": me_data.get("email", email), "name": me_data.get("name", name)}

    elif provider == "facebook":
        import httpx
        from app.config import FACEBOOK_APP_ID, FACEBOOK_APP_SECRET

        async with httpx.AsyncClient() as client:
            debug_res = await client.get(
                "https://graph.facebook.com/debug_token",
                params={"input_token": token, "access_token": f"{FACEBOOK_APP_ID}|{FACEBOOK_APP_SECRET}"},
            )
            debug_data = debug_res.json()
            if not debug_data.get("data", {}).get("is_valid"):
                raise HTTPException(status_code=401, detail="Invalid Facebook token")

            me_res = await client.get(
                "https://graph.facebook.com/me",
                params={"fields": "id,name,email", "access_token": token},
            )
            me_data = me_res.json()
            return {"email": me_data.get("email", email), "name": me_data.get("name", name)}

    raise HTTPException(status_code=400, detail="Invalid provider. Use: google or facebook")


@router.post("/social-login")
async def social_login(data: dict):
    db = get_db()
    provider = data.get("provider")
    token = data.get("token")

    if not provider or not token:
        raise HTTPException(status_code=400, detail="Provider and token required")

    profile = await verify_social_token(provider, token)
    email = profile["email"]
    name = profile["name"]

    user = await db.users.find_one({"email": email})
    if user:
        access_token = create_access_token(str(user["_id"]))
        return Token(access_token=access_token, user=user_to_out(user))

    return {"provider": provider, "token": token, "email": email, "name": name, "new_user": True}


@router.post("/social-register", response_model=Token)
async def social_register(data: dict):
    db = get_db()
    provider = data.get("provider")
    token = data.get("token")
    email = data.get("email", "")
    name = data.get("name", "")

    if not provider or not token or not email or not name:
        raise HTTPException(status_code=400, detail="Provider, token, email and name required")

    await verify_social_token(provider, token)
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    doc_num = data.get("document_number", "")
    if doc_num:
        doc_exists = await db.users.find_one({"document_number": doc_num})
        if doc_exists:
            raise HTTPException(status_code=409, detail="Document number already registered")

    user_doc = {
        "email": email,
        "name": name,
        "password_hash": "",
        "role": "paciente",
        "first_name": data.get("first_name", ""),
        "last_name": data.get("last_name", ""),
        "document_type": data.get("document_type", ""),
        "document_number": data.get("document_number", ""),
        "birth_date": data.get("birth_date", ""),
        "country": data.get("country", ""),
        "department": data.get("department", ""),
        "city": data.get("city", ""),
        "phone": data.get("phone", ""),
        "verified": True,
        "created_at": datetime.utcnow(),
    }
    result = await db.users.insert_one(user_doc)
    user = await db.users.find_one({"_id": result.inserted_id})
    access_token = create_access_token(str(result.inserted_id))

    return Token(access_token=access_token, user=user_to_out(user))


@router.get("/me", response_model=UserOut)
async def get_me(current_user: UserOut = Depends(get_current_user)):
    return current_user
