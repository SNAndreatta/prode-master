from werkzeug.security import generate_password_hash, check_password_hash
from fastapi import HTTPException, status, Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from database import get_db
from models.auth.auth_models import User
from blueprints.auth.jwt_handler import decode_jwt

def hash_password(password: str) -> str:
    """
    Genera un hash seguro usando PBKDF2-HMAC-SHA256 (por defecto de Werkzeug).
    """
    return generate_password_hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    """
    Verifica si la contraseña 'plain' coincide con el hash almacenado.
    """
    return check_password_hash(hashed, plain)

async def get_current_user(
    authorization: str = Header(..., description="Bearer token"),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Extract and validate user from JWT token. Returns user or raises HTTPException."""
    try:
        # Extract token from "Bearer <token>" format
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format"
            )
        
        token = authorization.split(" ")[1]
        
        # Decode JWT token
        payload = decode_jwt(token)
        user_id = int(payload.get("user_id"))
        
        # Get user from database
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

async def get_optional_current_user(
    authorization: Optional[str] = Header(None, description="Optional Bearer token"),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Attempt to extract and validate a user from the Authorization header.
    Returns None when no header is provided or when token is invalid.
    """
    if not authorization:
        return None
    try:
        if not authorization.startswith("Bearer "):
            return None
        token = authorization.split(" ")[1]
        payload = decode_jwt(token)
        user_id = int(payload.get("user_id"))
        user = await db.scalar(select(User).where(User.id == user_id))
        return user
    except Exception:
        return None
