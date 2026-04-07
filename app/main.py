from fastapi import FastAPI
from dotenv import load_dotenv
import uvicorn
import os


app = FastAPI(title="FastAPI Project")

load_dotenv()  # Loads .env contents into environment

api_key = os.getenv("API_KEY")


@app.get("/")
def root():
    return {"Hello": "World"}

if __name__ == "__main__":
    uvicorn.run(  "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )