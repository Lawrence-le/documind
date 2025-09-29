# rag-service\app\services\llm_service

import os
from openai import OpenAI
from loguru import logger

# from app.services.embedding_store import (
#     search_similar_documents,
# )

# Load OpenAI API key
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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


def generate_response_from_query(
    query: str, documents: list, model: str = "gpt-3.5-turbo", max_tokens: int = 512
):
    if not query:
        logger.warning("No query provided to LLM service.")
        return "Please provide a valid query."

    if not documents:
        logger.info("No relevant documents found for query. LLM call denied.")
        return "No relevant documents found to answer the question."
    else:
        context_docs = documents

    prompt = construct_prompt(query, context_docs)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        answer = response.choices[0].message.content
        logger.info(f"Generated response from LLM successfully | Answer : {answer}")
        return answer

    except Exception as e:
        logger.error(f"Failed to generate response from OpenAI: {e}")
        return f"Error: {e}"
