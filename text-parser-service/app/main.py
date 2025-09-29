#text-parser-service/main.py

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
import pdfplumber
from loguru import logger
from datetime import datetime
# import os
import io

from .publisher import AsyncRabbitMQPublisher, MessageModel

app = FastAPI()

publisher = AsyncRabbitMQPublisher()

@app.post("/parse")
async def parse(
    file: UploadFile = File(...), 
    user_id: str = Query("anonymous", description="ID of the user uploading the file")
    ):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    contents = await file.read()

    try:
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse PDF: {e}")

    if not full_text.strip():
        raise HTTPException(status_code=400, detail="No text extracted from PDF.")

    # Define the message payload
    message = MessageModel(
        text=full_text,
        source=file.filename,
        # user_id=user_id,
        # timestamp=datetime.utcnow().isoformat()
    )

    try:
        await publisher.publish(message)
        logger.info(f"Published parsed text from {file.filename} for user {user_id}")
    
    except Exception as e:
        logger.error(f"Failed to publish message: {e}")
        raise HTTPException(status_code=500, detail="Failed to publish message to queue.")

    result = {
    "filename": file.filename,
    "status": "Text parsed and published successfully"
    }
    
    logger.info(f"Returning response: {result}")

    return {
        "filename": file.filename,
        "status": "Text parsed and published successfully"
    }
    

@app.get("/")
async def root():
    return {"message": "Text Parser Service"}