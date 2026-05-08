from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.hash_password import hash_password
from app.schemas.login_schema import LoginRequest, TokenResponse
from app.models.employee_model import EmployeeDB
from app.models.department_model import DepartmentDB
from app.auth.hash_password import verify_password
from app.auth.jwt import create_access_token, get_current_user


router = APIRouter(prefix="/auth", tags=["Auth"])


# Employee login
@router.post("/login", response_model=TokenResponse)
def login(user: LoginRequest, db: Session = Depends(get_db)):
    db_user = db.query(EmployeeDB).filter(EmployeeDB.email == user.email).first()

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(user.pasword, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        data={
            "sub": str(db_user.emp_id),
            "name": db_user.emp_name,
            "email": db_user.email,
            "role_id": db_user.role_id,
            "dept_id":db_user.dept_id
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }



# Get current user
@router.get("/me")
def get_me(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):

    dept = db.query(DepartmentDB).filter(
        DepartmentDB.id == user["dept_id"]
    ).first()

    return {
        "user": user,
        "department_name": dept.dept_name if dept else None
    }






