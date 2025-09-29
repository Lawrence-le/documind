# llm-service\app\openai.py

import os
import openai
from loguru import logger
from rag_service.app.services.embedding_store import search_similar_documents  # adjust import path as needed

# Load OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY


def construct_prompt(query: str, documents: list) -> str:

    # Construct a prompt for the LLM combining user query and retrieved docs.

    context_text = "\n\n---\n\n".join([doc["content"] for doc in documents])
    
    prompt = (
        "You are an AI assistant. Use the following context to answer the question below. "
        "If the context does not contain the answer, respond accordingly.\n\n"
        f"Context:\n{context_text}\n\n"
        f"Question:\n{query}\n\n"
        "Answer:"
    )
    return prompt

def generate_response_from_query(query: str, top_k: int = 3, model: str = "gpt-4", max_tokens: int = 512):
    if not query:
        logger.warning("No query provided to LLM service.")
        return "Please provide a valid query."

    # Step 1: Search for similar documents in embedding store
    documents = search_similar_documents(query, top_k=top_k)
    if not documents:
        logger.info("No relevant documents found for query, proceeding without context.")
        context_docs = []
    else:
        context_docs = documents

    # Step 2: Build prompt using query + documents
    prompt = construct_prompt(query, context_docs)

    # Step 3: Call OpenAI API
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        answer = response.choices[0].message.content.strip()
        logger.info("Generated response from LLM successfully.")
        return answer

    except Exception as e:
        logger.error(f"Failed to generate response from OpenAI: {e}")
        return f"Error: {e}"
