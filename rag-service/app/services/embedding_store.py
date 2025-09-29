# rag-service/app/services/embedding_store.py
import os
import weaviate

# import weaviate.classes.config as wvcc
# from weaviate.connect import ConnectionParams
# from weaviate import WeaviateAsyncClient
# from weaviate.classes.config import Configure, Property, DataType
# from weaviate.classes.init import AdditionalConfig
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from loguru import logger

# Constants (Collection)
DOCUMENT_CLASS = "DocumentChunk"
QUERY_CLASS = "QueryVector"

# Define Weaviate URL
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://weaviate:8080")

# client: WeaviateAsyncClient = None
# WEAVIATE_HOST = os.getenv("WEAVIATE_HOST", "weaviate")
# WEAVIATE_HTTP_PORT = int(os.getenv("WEAVIATE_HTTP_PORT", 8080))
# WEAVIATE_GRPC_PORT = int(os.getenv("WEAVIATE_GRPC_PORT", 50052))

# Embedding model
# embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")


# Global client
client = None

# === Connection ===


def instantiate_and_connect() -> weaviate.Client:
    global client
    client = weaviate.Client(WEAVIATE_URL)

    if client.is_ready():
        logger.success("Connected to Weaviate.")
    else:
        raise RuntimeError("Failed to connect to Weaviate.")

    return client


# === Query Embedding (optional) ===
def embed_query(query: str) -> str:
    if not query:
        logger.warning("No query provided for embedding.")
        return "No query"

    try:
        document = Document(page_content=query)
        vector = embeddings.embed_query(document.page_content)
        logger.debug(f"Embedding query: len={len(vector)}, preview={vector[:5]}")

        # Insert Query into the class
        client.data_object.create(
            data_object={"content": document.page_content},
            class_name=QUERY_CLASS,
            vector=vector,
        )

        return "Query embedded and added to Weaviate"
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return f"Embedding error: {e}"


# === Semantic Search in Document Chunks ===
def search_similar_documents(query: str, top_k: int = 3):
    if not query:
        logger.warning("No query provided for search.")
        return []

    try:
        query_vector = embeddings.embed_query(query)

        response = (
            client.query.get(DOCUMENT_CLASS, ["content"])
            .with_near_vector({"vector": query_vector})
            .with_additional(["distance"])
            .with_limit(top_k)
            .do()
        )

        results = response["data"]["Get"].get(DOCUMENT_CLASS, [])
        documents = [
            {
                "content": obj.get("content", ""),
                "distance": obj.get("_additional", {}).get("distance", None),
            }
            for obj in results
        ]

        logger.info(f"Found {len(documents)} similar documents for query: '{query}'")
        return documents

    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        return []


# async def instantiate_and_connect() -> WeaviateAsyncClient:
#     global client
#     client = weaviate.Client(url=WEAVIATE_URL)
#     await client.connect()
#     ready = await client.is_ready()
#     logger.info(f"Connected to Weaviate: {ready}")
#     return client


# client = weaviate.WeaviateAsyncClient(
#     connection_params=ConnectionParams.from_params(
#         http_host=WEAVIATE_HOST,
#         http_port=WEAVIATE_HTTP_PORT,
#         http_secure=False,
#         grpc_host=WEAVIATE_HOST,
#         grpc_port=WEAVIATE_GRPC_PORT,
#         grpc_secure=False,
#     ),
#     additional_config=AdditionalConfig(grpc_timeout=10)  # Optional timeout
# )
# await client.connect()
# ready = await client.is_ready()
# logger.info(f"Connected to Weaviate: {ready}")
# return client

# # === Query Embedding (optional) ===
# async def embed_query(query: str) -> str:
#     if not query:
#         logger.warning("No query provided for embedding.")
#         return "No query"

#     try:
#         document = Document(page_content=query)
#         vector = embeddings.embed_query(document.page_content)
#         logger.debug(f"Embedding query: len={len(vector)}, preview={vector[:5]}")

#         # Get Collection class in Weaviate (Query Class)
#         collection = client.collections.get(QUERY_CLASS)
#         # Insert Query into Collection class (Query Class)
#         await collection.data.insert(
#             properties={"content": document.page_content},
#             vector=vector
#         )
#         return "Query embedded and added to Weaviate"
#     except Exception as e:
#         logger.error(f"Embedding failed: {e}")
#         return f"Embedding error: {e}"

# # === Semantic Search in Document Chunks ===
# async def search_similar_documents(query: str, top_k: int = 3):
#     if not query:
#         logger.warning("No query provided for search.")
#         return []

#     try:
#         query_vector = embeddings.embed_query(query)
#         collection = client.collections.get(DOCUMENT_CLASS)

#         results = await collection.query.near_vector(query_vector)\
#                                      .with_limit(top_k)\
#                                      .with_additional(['distance'])\
#                                      .do()

#         documents = [
#             {
#                 "content": obj.properties.get("content", ""),
#                 "distance": obj.additional.get("distance", None)
#             }
#             for obj in results.objects
#         ]

#         logger.info(f"Found {len(documents)} similar documents for query: '{query}'")
#         return documents
#     except Exception as e:
#         logger.error(f"Semantic search failed: {e}")
#         return []
