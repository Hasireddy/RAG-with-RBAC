import jwt
import os
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session



# Security configuration
# NOTE: In production, use environment variables for SECRET_KEY
# Example: SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_only")  # Replace with secure random value in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MIN = 60

# OAuth2 scheme - tokenUrl must match the login endpoint path
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256 with a random salt.

    Note: For production, consider using bcrypt or argon2 via passlib.
    This implementation uses hashlib for zero additional dependencies.

    Args:
        password: Plain text password

    Returns:
        Salted hash in format: salt$hash
    """
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((salt + password).encode())
    return f"{salt}${hash_obj.hexdigest()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hash in format: salt$hash

    Returns:
        True if password matches, False otherwise
    """
    try:
        salt, stored_hash = hashed_password.split("$")
        hash_obj = hashlib.sha256((salt + plain_password).encode())
        return secrets.compare_digest(hash_obj.hexdigest(), stored_hash)
    except ValueError:
        return False


def create_access_token(data: dict) -> str:
    """
    Create a JWT access token with expiration.

    Args:
        data: Dictionary containing claims (e.g., sub, role, user_id)

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MIN)
    to_encode.update({"exp": expire})

    return jwt.encode(
        payload=to_encode,
        key=SECRET_KEY,
        algorithm=ALGORITHM,
    )




def authenticate_user(db: Session, username: str, password: str) -> UserDB | None:
    """
    Authenticate a user by username and password.

    Args:
        db: Database session
        username: The username to authenticate
        password: The password to verify

    Returns:
        UserDB object if authenticated, None otherwise
    """
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> UserDB:
    """
    Validate JWT token and return the current user from database.

    Args:
        token: JWT token from Authorization header
        db: Database session

    Returns:
        UserDB object for the authenticated user

    Raises:
        HTTPException: If token is invalid, expired, or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(jwt=token, key=SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception

        user = get_user_by_username(db, username)
        if user is None:
            raise credentials_exception

        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise credentials_exception

