# ingestion-service/embedding_store.py

import weaviate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from loguru import logger
import os

# Initialize HuggingFace embeddings
# embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://weaviate:8080")

# Connect to Weaviate instance running locally
client = weaviate.Client(
    url=WEAVIATE_URL,  
)

# Define Weaviate class name for documents
DOCUMENT_CLASS = "DocumentChunk"

# Checks if the required Weaviate collection exists; creates it if missing to ensure proper schema setup.
def ensure_schema():
    try:
        schema = client.schema.get()
        classes = [cls["class"] for cls in schema.get("classes", [])]
        if DOCUMENT_CLASS not in classes:
            class_obj = {
                "class": DOCUMENT_CLASS,
                "vectorIndexType": "hnsw",
                "vectorizer": "none",  # We provide embeddings ourselves
                "properties": [
                    {"name": "content", "dataType": ["text"]},
                ],
            }
            client.schema.create_class(class_obj)
            logger.info(f"Created Weaviate schema class '{DOCUMENT_CLASS}'")
        else:
            logger.info(f"Weaviate schema class '{DOCUMENT_CLASS}' already exists")
    except Exception as e:
        logger.error(f"Failed to ensure schema: {e}")

async def embed_and_store(chunks: list[str]):
    try:
        if not chunks:
            logger.warning("No chunks to embed. Skipping embedding step.")
            return

        # Create Document objects
        docs = [Document(page_content=chunk) for chunk in chunks]

        # Get embeddings for all chunks
        vectors = embeddings.embed_documents([doc.page_content for doc in docs])

        for i, (doc, vector) in enumerate(zip(docs, vectors)):
            logger.debug(f"Embedding chunk {i+1}: len={len(vector)}, preview={vector[:5]}")

            # Prepare the object data with chunk content
            obj = {
                "content": doc.page_content,
            }

            # Add the object with own vector to Weaviate
            client.data_object.create(
                data_object=obj,
                class_name=DOCUMENT_CLASS,
                vector=vector,
            )

        logger.success(f"Stored {len(docs)} chunks in Weaviate vector DB")

    except Exception as e:
        logger.error(f"Embedding and storing failed: {e}")
