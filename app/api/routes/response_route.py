from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from openai import OpenAI
from dotenv import load_dotenv
import os
import uuid
import traceback


from app.schemas.response_schema import  ResponseSchema
from app.schemas.query_schema import QueryRequest
from app.database.session import get_db
from app.models.response_model import AIResponseDB
#from app.rag.embed_documents import get_response
from app.rag.get_api_response import get_response
from app.auth.jwt import get_current_user
from app.models.messages_model import  ChatMessage


# Load environment variables
load_dotenv()
API_KEY=os.getenv("API_KEY")

router = APIRouter(prefix="/chatbot", tags=["OpenAIAPIResponse"])

client = OpenAI(api_key=API_KEY)

templates = Jinja2Templates(directory="frontend/templates")


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
@router.post("/", response_model=ResponseSchema)
def create_response(payload: QueryRequest, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Gets response from openai API"""

    try:
        query = payload.query.strip()

        if not query:
            raise HTTPException(
                status_code=400,
                detail="Query cannot be empty"
            )

        #User details
        emp_id =user.get("emp_id")
        emp_name = user.get("emp_name")
        email = user.get("email")
        role_id = user.get("role_id")

        # Department details
        dept_id = user.get("dept_id")

        print("USER:", emp_id)
        print("NAME:", emp_name)
        print("EMAIL:", email)
        print("ROLE:", role_id)
        print("DEPARTMENT:", dept_id)

        # Session handling
        session_id = payload.session_id

        if not session_id:
            session_id = str(uuid.uuid4())

        response_text = get_response(query=query, session_id=session_id)

        if not  response_text:
            response_text = "No response generated."

        # Save response in DB
        print("TYPE:", type(response_text))
        #ai_response = AIResponseDB(session_id=session_id, emp_id=emp_id, query=query, result=response_text)
        # Save user message
        user_message = ChatMessage(
            session_id=session_id,
            emp_id=emp_id,
            role="user",
            message=query
        )

        db.add(user_message)

        # Save assistant message
        assistant_message = ChatMessage(
            session_id=session_id,
            emp_id=emp_id,
            role="assistant",
            message=response_text
        )

        db.add(assistant_message)
        #db.add(ai_response)
        db.commit()
        db.refresh(user_message)
        db.refresh(assistant_message)
        #print(ai_response)
        #return ai_response
        # Return response + session_id
        return {
            "session_id": session_id,
            "query": query,
            "result": response_text
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )



@router.get("/", name="chatbot")
def render_chat(request:Request):
    return templates.TemplateResponse(
        request=request,
        name="chatbot.html",
    )
