from fastapi import APIRouter, Depends, HTTPException, Request,status
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse,  RedirectResponse


from app.database.session import get_db
from app.auth.hash_password import hash_password
from app.schemas.login_schema import LoginRequest, TokenResponse
from app.models.employee_model import EmployeeDB
from app.models.department_model import DepartmentDB
from app.auth.hash_password import verify_password
from app.auth.jwt import create_access_token, get_current_user, authenticate_user
from app.database.session import get_db



router = APIRouter(prefix="", tags=["Auth"])
#router = APIRouter()

templates = Jinja2Templates(directory="frontend/templates")


# Employee login
@router.post("/token", response_model=TokenResponse)
def login(request: Request,form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
      Authenticate user and return JWT access token.
      Use the returned token in the Authorization header as: Bearer <token>
      Render User details
      """
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    dept_names = [d.dept_name.lower() for d in user.departments] if user.departments else []
    print(dept_names)

    data={
            "emp_id": str(user.emp_id),
            "emp_name": user.emp_name,
            "email": user.email,
            "job_title": user.job_title,
            "dept_id": user.dept_id,
            "departments": dept_names
        }

    token = create_access_token(data=data)

    print("USER:", data["emp_id"])
    print("NAME:", data["emp_name"])
    print("EMAIL:", data["email"])
    print("ROLE:", data["job_title"])
    print("DEPARTMENT ID:", data["dept_id"])
    print("DEPARTMENTS:", data["departments"])

    request.session["user"] = data
    return {"access_token": token, "token_type": "bearer", "data": data}



@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Render the login page"""
    return templates.TemplateResponse(
        request=request, name="login.html"
    )



@router.get("/logout", response_class=HTMLResponse)
def logout(request: Request):
    """
    Render logout page
    """
    return templates.TemplateResponse(
        request=request, name="logout.html"
    )












