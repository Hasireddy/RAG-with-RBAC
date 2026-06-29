import pydantic
from fastapi import APIRouter
from app.api.routes import company_route, department_route, employee_route,response_route, login_route

pydantic.root_validator = pydantic.model_validator
api_router = APIRouter()

api_router.include_router(company_route.router)
api_router.include_router(department_route.router)
api_router.include_router(employee_route.router)
api_router.include_router(response_route.router)
api_router.include_router(login_route.router)
