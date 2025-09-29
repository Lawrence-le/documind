# rag-service\app\routes\rag.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger


from app.services.embedding_store import embed_query, search_similar_documents
from app.services.llm_service import generate_response_from_query

# from app.services.vectorstore import retrieve_relevant_chunks

router = APIRouter()


class PromptRequest(BaseModel):
    query: str


@router.post("/reply")
async def get_answer(data: PromptRequest):
    try:
        # Step 1: Embed the incoming user query (optional but included)
        embed_result = embed_query(data.query)

        # Step 2: Search the vector DB for top-k relevant document chunks
        relevant_docs = search_similar_documents(data.query, top_k=3)

        # sample output:
        """
        [
            {
                "content": "Sentence",
                "distance": 0.12
            },
        ]
        """

        # Step 3: Generate a response using LLM (OpenAI) with context
        response = generate_response_from_query(data.query, relevant_docs)

        logger.info(f"Relevant docs for query '{data.query}':\n\n {relevant_docs}\n\n")

        return {
            "embedding_status": embed_result,
            # "relevant_documents": relevant_docs,
            "answer": response,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
