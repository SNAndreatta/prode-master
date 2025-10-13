from datetime import datetime, timedelta, timezone
import os
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from settings import JWT_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS

if not JWT_KEY:
    raise ValueError("JWT_KEY environment variable is not set")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, JWT_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, JWT_KEY, algorithm=ALGORITHM)

def decode_jwt(token: str) -> dict:
    """
    Devuelve el payload decodificado o lanza excepciones manejables.
    """
    try:
        payload = jwt.decode(token, JWT_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise ValueError("Token expirado")
    except InvalidTokenError:
        raise ValueError("Token inválido")
