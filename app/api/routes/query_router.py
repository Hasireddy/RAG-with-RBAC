from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from openai import OpenAI
from dotenv import load_dotenv
import os
import uuid
import traceback
import json

from app.schemas.response_schema import ResponseSchema
from app.schemas.query_schema import QueryRequest
from app.database.session import get_db
from app.models.response_model import AIResponseDB
# from app.rag.embed_documents import get_response
from app.rag.get_api_response import get_response
from app.auth.jwt import get_current_user
from app.models.messages_model import ChatMessage
from app.rag.get_api_response import get_response
from app.auth.jwt import get_current_user
from app.models.messages_model import ChatMessage


# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")

router = APIRouter(prefix="/chatbot", tags=["OpenAIAPIResponse"])

client = OpenAI(api_key=API_KEY)

templates = Jinja2Templates(directory="frontend/templates")


@router.post("/chat", response_model=ResponseSchema)
def chat(payload: QueryRequest, db: Session = Depends(get_db), user:dict = Depends(get_current_user)):
    #Detect mode
    mode = detect_query_type_llm(query)
    print(f"Detected mode:{mode}")
