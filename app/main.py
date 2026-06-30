import os
import uvicorn

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from app.database.init_db import init_db

from app.api.api import api_router
from starlette.middleware.sessions import SessionMiddleware


# Load environment variables
load_dotenv()
API_KEY=os.getenv("API_KEY")


# Initialize the database
@asynccontextmanager
async def lifespan(app:FastAPI):
    init_db()
    yield



# Create FastAPI app
app = FastAPI(
    title="RAG with Role Based Access Control",
    #title="RAG with Role Based Access Control",
    description="Secure Role-Based Data Retrieval Bot",
    lifespan=lifespan
  )

# Middleware
app.add_middleware(SessionMiddleware,secret_key=API_KEY)

# Include all routes
app.include_router(api_router)

#Templates and static folders
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Renders and returns the home page template"""
    try:
        return templates.TemplateResponse(
            request=request, name="index.html"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Template rendering failed: {e}"
        )



if __name__ == "__main__":
    uvicorn.run(
  "main:app",
        #host="127.0.0.1",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
