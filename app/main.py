from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from openai import OpenAI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import uvicorn

from app.database.init_db import init_db
from app.api.api import api_router



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
    description="A private chatbot for a company",
    lifespan=lifespan
  )


# Include all routes
app.include_router(api_router)

#Templates and static folders
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")



@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html"
    )



if __name__ == "__main__":
    uvicorn.run(  "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
