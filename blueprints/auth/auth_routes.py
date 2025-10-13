from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta
from database import get_db
from models.auth.auth_models import Token, User
from blueprints.auth.utils import hash_password, verify_password
from blueprints.auth.jwt_handler import create_access_token, create_refresh_token, decode_jwt

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserRead(BaseModel):
    id: int
    username: str           
    email: EmailStr
    class Config:
        orm_mode = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserLogin(BaseModel):
    email: EmailStr
    password: str


@auth_router.post("/register", response_model=UserRead)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Verificar si el email ya existe
    existing_email = await db.scalar(select(User).where(User.email == user_data.email))
    if existing_email:
        raise HTTPException(status_code=400, detail="Email ya registrado")
    
    # Verificar si el username ya existe
    existing_username = await db.scalar(select(User).where(User.username == user_data.username))
    if existing_username:
        raise HTTPException(status_code=400, detail="Username ya registrado")

    user = User(
        email=user_data.email,
        username=user_data.username,   # guardamos el username
        hashed_password=hash_password(user_data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@auth_router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin, 
    user_agent: str | None = Header(None),  # capturamos User-Agent
    db: AsyncSession = Depends(get_db)
):
    # Buscar usuario por username
    user = await db.scalar(select(User).where(User.email == user_data.email))
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    # Crear tokens
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    # Guardar refresh token en la base con User-Agent
    token_entry = Token(
        user_id=user.id,
        refresh_token=refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=7),
        revoked=False,
        user_agent=user_agent
    )
    db.add(token_entry)
    await db.commit()

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_jwt(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Tipo de token inválido")
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    user_id = int(payload.get("sub"))
    db_token = await db.scalar(
        select(Token).where(
            Token.refresh_token == refresh_token,
            Token.revoked == False,
            Token.expires_at > datetime.utcnow()
        )
    )

    if not db_token:
        raise HTTPException(status_code=401, detail="Refresh token inválido o expirado")

    new_access_token = create_access_token({"sub": str(user_id)})
    return {"access_token": new_access_token, "refresh_token": refresh_token, "token_type": "bearer"}


# --- LOGOUT ---
@auth_router.post("/logout")
async def logout(refresh_token: str, db: AsyncSession = Depends(get_db)):
    db_token = await db.scalar(select(Token).where(Token.refresh_token == refresh_token))
    if not db_token:
        raise HTTPException(status_code=404, detail="Token no encontrado")

    # Revocar token
    await db.execute(
        update(Token).where(Token.id == db_token.id).values(revoked=True)
    )
    await db.commit()

    return {"detail": "Sesión cerrada correctamente"}
