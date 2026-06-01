import os
from fastapi.security import HTTPBearer
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from typing import Optional
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.models.employee_model import EmployeeDB
from app.auth.hash_password import verify_password


SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_only")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = HTTPBearer()



def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    expire = (
        datetime.now(timezone.utc) + expires_delta
        if expires_delta
        else datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({
        "exp": expire,
        "type": "access"
    })

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)




def get_user_by_email(db: Session, email: str) -> EmployeeDB | None:
    """
    Retrieve a user from the database by email.

    Args:
        db: Database session
        username: Username to look up

    Returns:
        UserDB object if found, None otherwise
    """
    return db.query(EmployeeDB).filter(EmployeeDB.email == email).first()



def authenticate_user(db: Session, email: str, password: str) -> EmployeeDB | None:
    """
    Authenticate a user by username and password.

    Args:
        db: Database session
        username: The username to authenticate
        password: The password to verify

    Returns:
        UserDB object if authenticated, None otherwise
    """
    password = password.strip()
    user = get_user_by_email(db, email)

    if not user:
        print("NO USER FOUND")
        return None


    valid = verify_password(password, user.hashed_password)

    if not valid:
        return None

    return user


def get_current_user(token=Depends(oauth2_scheme)):
    try:
        jwt_token = token.credentials
        payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=[ALGORITHM])

        return {
            "emp_id": payload.get("emp_id"),
            "emp_name": payload.get("emp_name"),
            "email": payload.get("email"),
            #"role_id": payload.get("role_id"),
            "job_title": payload.get("job_title"),
            "dept_id": payload.get("dept_id"),
            "departments": payload.get("departments")
        }

    except JWTError as e:
        print(" JWT ERROR:", str(e))
        raise HTTPException(status_code=401, detail="Token expired or invalid")




