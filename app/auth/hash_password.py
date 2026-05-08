import hashlib
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def normalize_password(password: str) -> str:
    # SHA256 reduces any size input to fixed 32 bytes
    return hashlib.sha256(password.encode()).hexdigest()


def hash_password(password: str) -> str:
    return pwd_context.hash(normalize_password(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(
        normalize_password(plain_password),
        hashed_password
    )