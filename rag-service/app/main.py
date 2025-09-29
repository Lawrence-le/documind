# rag-service\app\main.py

from fastapi import FastAPI
from app.routes import rag
from app.services.embedding_store import instantiate_and_connect

app = FastAPI()

# Include your API router with /rag prefix
app.include_router(rag.router, prefix="/rag")

@app.on_event("startup")
def startup_event():
    # Connect to Weaviate
    instantiate_and_connect()

@app.get("/")
async def root():
    return {"message": "RAG Service is running"}