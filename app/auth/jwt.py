import os
from fastapi.security import HTTPBearer
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from typing import Optional
from jose import jwt, JWTError


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




def get_current_user(token=Depends(oauth2_scheme)):
    try:
        jwt_token = token.credentials
        payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload

    except JWTError as e:
        print(" JWT ERROR:", str(e))
        raise HTTPException(status_code=401, detail="Token expired or invalid")




