from fastapi import APIRouter, Depends, HTTPException, Request,status
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse


from app.database.session import get_db
from app.auth.hash_password import hash_password
from app.schemas.login_schema import LoginRequest, TokenResponse
from app.models.employee_model import EmployeeDB
from app.models.department_model import DepartmentDB
from app.auth.hash_password import verify_password
from app.auth.jwt import create_access_token, get_current_user, authenticate_user



router = APIRouter(prefix="", tags=["Auth"])
#router = APIRouter()

templates = Jinja2Templates(directory="frontend/templates")


# Employee login
@router.post("/token", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
      Authenticate user and return JWT access token.
      Use the returned token in the Authorization header as: Bearer <token>
      """
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        data={
            "sub": str(user.emp_id),
            "name": user.emp_name,
            "email": user.email,
            "role_id": user.role_id,
            "dept_id": user.dept_id
        }
    )

    return {"access_token": token, "token_type": "bearer"}




@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="login.html"
    )


# Get current user
@router.get("/me")
def get_me(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get information about the currently authenticated user."""

    dept = db.query(DepartmentDB).filter(
        DepartmentDB.id == user["dept_id"]
    ).first()

    return {
        "user": user,
        "department_name": dept.dept_name if dept else None
    }






