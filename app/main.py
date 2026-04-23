from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
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


client = OpenAI(api_key=API_KEY)

class Step(BaseModel):
    explanation: str
    output: str

class MathReasoning(BaseModel):
    steps: list[Step]
    final_answer: str


@app.get("/")
def root():
    try:
       response = client.responses.create(
           model="gpt-4o-mini",
           temperature=0.7,
           input=[
               {
                   "role": "system",
                   "content": "You are a creative assistant"
               },
               {
                   "role": "user",
                   "content": "write a 50 word story about unicorn"
               }
           ]
       )
       return {"result": response.output_text}

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    uvicorn.run(  "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )

