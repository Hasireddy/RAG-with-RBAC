from fastapi import APIRouter
from app.api.routes import company_route

api_router = APIRouter()

api_router.include_router(company_route.router)