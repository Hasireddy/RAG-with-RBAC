import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from spacy.cli.benchmark_speed import count_tokens
from sqlalchemy.orm import Session
from openai import OpenAI
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import json
import traceback
from fastapi import Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse


from app.schemas.response_schema import ResponseSchema
from app.schemas.query_schema import QueryRequest
from app.database.session import get_db
from app.rag.get_api_response import get_response
from app.auth.jwt import get_current_user
from app.models.messages_model import ChatMessage
from app.agent.nodes import run_agent
from app.rag.get_api_response import stream_response
from app.agent.query_classifier import detect_query_type_llm

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")

router = APIRouter(prefix="/chatbot", tags=["OpenAIAPIResponse"])

client = OpenAI(api_key=API_KEY)

templates = Jinja2Templates(directory="frontend/templates")
llm = ChatOpenAI(model="gpt-4o",api_key=API_KEY)
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
def create_response(payload: QueryRequest, db: Session = Depends(get_db), user:dict = Depends(get_current_user)):
    """Gets response from openai API"""

    try:
        # Generate session id if not provided in payload
        query = payload.query.strip()

        # User details
        emp_id = user.get("emp_id")
        emp_name = user.get("emp_name")
        email = user.get("email")
        job_title = user.get("job_title")


        # Department details
        dept_id = user.get("dept_id")
        departments = user.get("departments")

        # Session handling
        session_id = f"user_{emp_id}"

        #Control User query's length
        num_tokens = llm.get_num_tokens(query)
        print("NUM_TOKENS", num_tokens)
        if num_tokens > 300:
            raise HTTPException(
                status_code=400,
                detail="Query length exceeded more than 300 tokens"
            )


        if not query:
            raise HTTPException(
                status_code=400,
                detail="Query cannot be empty"
            )



        response_text = run_agent(
            query=query,
            session_id=session_id,
            emp_id=emp_id,
            emp_name=emp_name,
            email=email,
            job_title=job_title,
            departments=departments,
            dept_id=dept_id
        )

        if response_text is None:
            response_text = "No response generated."

        # Save response in DB
        # ai_response = AIResponseDB(session_id=session_id, emp_id=emp_id, query=query, result=response_text)
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
            message=json.dumps(response_text)
            #message=response_text
        )

        db.add(assistant_message)
        # db.add(ai_response)
        db.commit()
        db.refresh(user_message)
        db.refresh(assistant_message)

        return {
            "session_id": session_id,
            "messages": [
                {
                    "role": assistant_message.role,
                    "message": {"content": response_text["message"]["content"]},
                    "created_at": assistant_message.created_at
                }
            ]
        }

    except HTTPException:
        raise

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Something went wrong while generating response"
        )



"""@router.get("/", name="chatbot")
def render_chat(request:Request):
    return templates.TemplateResponse(
        request=request,
        name="chatbot.html",
    )
"""


@router.get("/", name="user-details")
def render_chat(request: Request):
    return templates.TemplateResponse(
        request,
        "user_details.html",
        {"user": request.session.get("user")}

    )


# Helper function to save the chat logs into the DB in the background
def save_chat_to_db(session_id: str, emp_id: str, query: str, final_answer: str):
    """Executes DB writes asynchronously after the stream finishes to keep endpoint low-latency."""
    db = next(get_db())  # Get a fresh session instance for background context
    try:
        user_message = ChatMessage(
            session_id=session_id,
            emp_id=emp_id,
            role="user",
            message=query
        )
        db.add(user_message)

        # Mirroring your original payload wrapper logic for database consistency
        structured_response = {"message": {"content": final_answer}}
        assistant_message = ChatMessage(
            session_id=session_id,
            emp_id=emp_id,
            role="assistant",
            message=json.dumps(structured_response)
        )
        db.add(assistant_message)
        db.commit()
    except Exception as db_err:
        logging.error(f"Failed background DB save: {db_err}")
    finally:
        db.close()



@router.post("/stream")
def generate_stream(payload: QueryRequest, db: Session = Depends(get_db), user:dict = Depends(get_current_user)):
            """Gets response from openai API"""
            # Generate session id if not provided in payload
            query = payload.query.strip()

            # User details
            emp_id = user.get("emp_id")
            emp_name = user.get("emp_name")
            email = user.get("email")
            job_title = user.get("job_title")

            # Department details
            dept_id = user.get("dept_id")
            departments = user.get("departments")

            # Session handling
            session_id = f"user_{emp_id}"

            # Control User query's length
            num_tokens = llm.get_num_tokens(query)
            print("NUM_TOKENS", num_tokens)

            if num_tokens > 300:
                raise HTTPException(
                    status_code=400,
                    detail="Query length exceeded more than 300 tokens"
                )

            if not query:
                raise HTTPException(
                    status_code=400,
                    detail="Query cannot be empty"
                )

            def stream_wrapper():
                full_answer_list = []

                # Call your refactored streaming backend function
                try:
                    # Route structured/analytical queries (counts, totals, employee
                    # data, etc.) to the SQL agent; everything else streams via RAG.
                    query_type = detect_query_type_llm(query)
                    logging.info(f"Query type classified as: {query_type}")

                    if query_type == "SQL":
                        # The SQL/agent path is not token-streamable; run it and emit
                        # the finished answer as a single SSE frame.
                        result = run_agent(
                            query=query,
                            session_id=session_id,
                            emp_id=emp_id,
                            emp_name=emp_name,
                            email=email,
                            job_title=job_title,
                            departments=departments,
                            dept_id=dept_id
                        )

                        answer = result["message"]["content"] if result else "No response generated."
                        full_answer_list.append(answer)
                        yield f'data: {json.dumps({"token": answer})}\n\n'
                    else:
                        # RAG path: stream tokens from the LLM as they are produced.
                        for chunk_str in stream_response(
                                query=query,
                                session_id=session_id,
                                emp_name=emp_name,
                                email=email,
                                departments=departments,
                        ):
                            try:
                                chunk_data = json.loads(chunk_str)
                                # Accumulate raw text for the eventual database commit.
                                if "token" in chunk_data:
                                    full_answer_list.append(chunk_data["token"])
                                elif "answer" in chunk_data:
                                    # Guard-rail messages (UNAUTHORIZED / NOT_FOUND).
                                    full_answer_list.append(chunk_data["answer"])
                            except Exception:
                                # Non-JSON fallback chunk; forward it unchanged.
                                pass

                            # Yield chunks using standard Server-Sent Events (SSE) format
                            yield f"data: {chunk_str}\n\n"

                finally:
                    # 2. Schedule background database save execution once stream finishes
                    final_answer = "".join(full_answer_list) if full_answer_list else "No response generated."
                    save_chat_to_db(session_id, emp_id, query, final_answer)
                    #yield "data: [DONE]\n\n"

            # 3. Return immediate Streaming Response to client
            return StreamingResponse(stream_wrapper(), media_type="text/event-stream")
