from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from dotenv import load_dotenv
import os
import uvicorn

from app.database.init_db import init_db
from app.api.api import api_router


# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")


# Initialize the database
@asynccontextmanager
async def lifespan(app):
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


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "API is running"
    }


if __name__ == "__main__":
    uvicorn.run(  "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )