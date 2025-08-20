import os
import datetime
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

JWT_SECRET = os.getenv("JWT_SECRET", "super-secret")
JWT_ALGO = "HS256"
JWT_EXPIRE = 60 * 60 * 24  # 24 ore

def create_jwt(payload, expires_in=JWT_EXPIRE):
    payload["exp"] = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

def decode_jwt(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return check_password_hash(hashed, password)