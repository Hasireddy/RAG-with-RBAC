from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from openai import OpenAI
from dotenv import load_dotenv
import os

from app.schemas.response_schema import  ResponseSchema
from app.database.session import get_db
from app.models.response_model import AIResponseDB
from app.rag.embed_documents import get_response


# Load environment variables
load_dotenv()
API_KEY=os.getenv("API_KEY")

router = APIRouter()

client = OpenAI(api_key=API_KEY)


# Get a response
@router.get("/chatbot", response_model=ResponseSchema)
def create_response(db: Session = Depends(get_db)):
    try:
        """response = client.responses.create(
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
        )"""
        response_text =  get_response()
        print(response_text)

        if not response_text:
            response_text = "No response generated."

        # Save response in DB
        ai_response = AIResponseDB(result=response_text)
        db.add(ai_response)
        db.commit()
        db.refresh(ai_response)

        return ai_response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )





