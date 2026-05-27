from fastapi import APIRouter, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from openai import OpenAI
from dotenv import load_dotenv
import os

from app.database.session import get_db
#from agent.query_classifier import detect_query_type_llm
from app.schemas.query_schema import QueryRequest
from app.schemas.response_schema import ResponseSchema

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")

router = APIRouter(prefix="/chatbot", tags=["OpenAIAPIResponse"])

client = OpenAI(api_key=API_KEY)

templates = Jinja2Templates(directory="frontend/templates")

#def chat(payload: QueryRequest, db: Session = Depends(get_db), user:dict = Depends(get_current_user)):
@router.post("/chat", response_model=ResponseSchema)
def chat(payload: QueryRequest, db: Session = Depends(get_db)):
    query = payload.query.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty"
        )

    # Session handling
    #session_id = payload.session_id

    #if not session_id:
        #session_id = str(uuid.uuid4())

    #Detect mode
    mode = detect_query_type_llm(query)
    ai_answer = mode
    print(f"Detected mode:{mode}")
    return {
        #"session_id": session_id,
        "session_id": "1",
        "answer": ai_answer,
        "mode": mode
    }



