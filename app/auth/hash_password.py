import hashlib
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

"""def normalize_password(password: str) -> str:
    # SHA256 reduces any size input to fixed 32 bytes
    return hashlib.sha256(password.encode()).hexdigest()"""



def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    try:
        return pwd_context.verify(
                plain_password,
                hashed_password
            )
    except Exception:
        return False