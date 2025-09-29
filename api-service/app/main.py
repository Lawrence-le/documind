# api-service/main.py (FastAPI app)

from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .publisher import AsyncRabbitMQPublisher, MessageModel
from datetime import datetime
from loguru import logger
import httpx
import os

app = FastAPI()

origins = os.getenv("CORS_ORIGINS", "")
if origins:
    origins = origins.split(",")
else:
    origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEXT_PARSER_URL = os.getenv("TEXT_PARSER_URL")
OCR_SERVICE_URL = os.getenv("OCR_SERVICE_URL")
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL")
# INGESTION_URL = "http://injestion-service:8000/ingest_text"


class PostRequest(BaseModel):
    query: str


@app.post("/reply")
async def reply(request: PostRequest):
    async with httpx.AsyncClient() as client:
        try:
            if not RAG_SERVICE_URL:
                raise HTTPException(
                    status_code=500, detail="RAG_SERVICE_URL not configured"
                )

            response = await client.post(RAG_SERVICE_URL, json=request.dict())
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"RAG service error: {response.text}",
                )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"RAG service error: {str(e)}")


@app.post("/upload_docs")
async def upload_docs(docs: list[UploadFile] = File(...)):
    async with httpx.AsyncClient() as client:
        results = []
        print(f"TEXT_PARSER_URL: {TEXT_PARSER_URL}")
        for doc in docs:
            filename = doc.filename.lower()
            file_bytes = await doc.read()
            text_content = ""

            if filename.endswith(".pdf"):
                # Try text-parser service first
                parser_resp = await client.post(
                    TEXT_PARSER_URL,
                    files={"file": (doc.filename, file_bytes, doc.content_type)},
                )
                if parser_resp.status_code == 200:
                    results.append(
                        {"filename": doc.filename, "status": "Processed by text-parser"}
                    )
                else:
                    print(
                        f"[ERROR] text-parser failed: {parser_resp.status_code} - {parser_resp.text}"
                    )
                    # Fallback to OCR
                    ocr_resp = await client.post(
                        OCR_SERVICE_URL,
                        files={"file": (doc.filename, file_bytes, doc.content_type)},
                    )
                    if ocr_resp.status_code == 200:
                        results.append(
                            {
                                "filename": doc.filename,
                                "status": "Processed by OCR",
                            }
                        )
                    else:
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to process {doc.filename} using both services.",
                        )
            else:
                # Non-PDF files handled by OCR
                allowed_ocr_formats = [".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif"]
                if any(filename.endswith(ext) for ext in allowed_ocr_formats):
                    ocr_resp = await client.post(
                        OCR_SERVICE_URL,
                        files={"file": (doc.filename, file_bytes, doc.content_type)},
                    )
                    if ocr_resp.status_code == 200:
                        results.append(
                            {
                                "filename": doc.filename,
                                "status": "Processed by OCR",
                            }
                        )
                    else:
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to process {doc.filename} using OCR.",
                        )
                else:
                    raise HTTPException(
                        status_code=400, detail=f"Unsupported file type: {doc.filename}"
                    )

        return {"results": results}


class PostRequest(BaseModel):
    text: str
    user_id: str


@app.post("/send-message")
async def send_message(request: PostRequest):
    message = MessageModel(
        text=request.text,
        user_id=request.user_id,
        timestamp=datetime.utcnow().isoformat(),
    )
    try:
        await publisher.publish(message)
        return {"status": "Message queued successfully"}
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


publisher = AsyncRabbitMQPublisher()


@app.on_event("startup")
async def startup_event():
    await publisher.connect()


@app.on_event("shutdown")
async def shutdown_event():
    await publisher.close()


@app.get("/")
async def root():
    return {"message": "API Service"}
