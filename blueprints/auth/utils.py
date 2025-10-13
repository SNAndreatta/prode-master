from werkzeug.security import generate_password_hash, check_password_hash

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
