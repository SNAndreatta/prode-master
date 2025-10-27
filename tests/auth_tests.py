import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

# === Config in-memory DB ===
DATABASE_URL = "sqlite+aiosqlite:///:memory:"
Base = declarative_base()

# === Minimal User model ===
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

# === Minimal JWT settings ===
JWT_KEY = "testsecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

# === Auth functions ===
def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return check_password_hash(hashed, plain)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, JWT_KEY, algorithm=ALGORITHM)

def decode_jwt(token: str) -> dict:
    from jwt import ExpiredSignatureError, InvalidTokenError
    try:
        return jwt.decode(token, JWT_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise ValueError("Token expired")
    except InvalidTokenError:
        raise ValueError("Invalid token")

# === Fixtures for async DB ===
@pytest.fixture(scope="function")
async def session():
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        yield db
    await engine.dispose()

# === Tests ===
@pytest.mark.asyncio
async def test_password_hashing():
    password = "supersecret"
    hashed = hash_password(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrong", hashed)

@pytest.mark.asyncio
async def test_jwt_create_decode():
    data = {"user_id": 1}
    token = create_access_token(data)
    payload = decode_jwt(token)
    assert payload["user_id"] == 1
    assert payload["type"] == "access"

@pytest.mark.asyncio
async def test_user_crud(session: AsyncSession):
    # Create user
    user = User(email="test@example.com", username="testuser", hashed_password=hash_password("pass123"))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    # Fetch user by ID
    result = await session.get(User, user.id)
    assert result.username == "testuser"
    assert verify_password("pass123", result.hashed_password)
    
    # JWT generation and decode
    token = create_access_token({"user_id": result.id})
    payload = decode_jwt(token)
    assert payload["user_id"] == result.id
