from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

from fastapi.responses import JSONResponse
from app.schemas.response_schema import  ResponseSchema
from app.database.session import get_db
from app.models.response_model import AIResponseDB
#from app.rag.embed_documents import get_response
from app.rag.get_api_response import get_response


# Load environment variables
load_dotenv()
API_KEY=os.getenv("API_KEY")

router = APIRouter(prefix="/chatbot", tags=["OpenAIAPIResponse"])

client = OpenAI(api_key=API_KEY)

#query = "What is Python?"
#query="List all employees details in sales department who took more then 10 leaves?"
query="Explain Public Holidays Policy?"
#query="Explain employee onboarding benefits?"

# Get a response
"""@router.get("/chatbot", response_model=ResponseSchema)
def create_response(db: Session = Depends(get_db)):
    

    try:
        response_text =  get_response(query)

        try:
            parsed_result = json.loads(response_text)
        except (json.JSONDecodeError, TypeError):
            parsed_result = response_text

        if not  parsed_result:
            parsed_result = "No response generated."

        # Save response in DB
        db_result = json.dumps(parsed_result) if isinstance(parsed_result, (dict, list)) else str(parsed_result)
        ai_response = AIResponseDB(result=db_result)
        db.add(ai_response)
        db.commit()
        db.refresh(ai_response)

        # Return properly parsed JSON or text
        try:
            return {"id": ai_response.id, "result": json.loads(ai_response.result)}
        except json.JSONDecodeError:
            return {"id": ai_response.id, "result": ai_response.result}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )"""





# Get a response
@router.get("/", response_model=ResponseSchema)
def create_response(db: Session = Depends(get_db)):
    """Gets response from openai API"""

    try:
        response_text =  get_response(query)
        if not  response_text:
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



