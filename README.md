# DocuMind

Documind is an intelligent document processing platform that leverages AI-powered text embedding, semantic search, and messaging to efficiently ingest and retrieve relevant information from large volumes of text.

It integrates vector databases, chunking methods, and scalable APIs to deliver context-aware document insights for enhanced knowledge management.

## File Structure (Microservices)

```
[To Be Updated]
documind-microservices/
├── api-service/
|   ├── app/
│   |   ├── __init__.py
│   |   ├── publisher.py
│   |   └── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── tests/
│   └── README.md
|
├── text-parser-service/
│   ├── app/
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── tests/
│   └── README.md
|
├── ocr-service/
│   ├── app/
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── tests/
│   └── README.md
|
├── injestion-service/
|   ├── app/
│   |   ├── __init__.py
│   |   ├── consumer.py
│   |   └── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── tests/
│   └── README.md
│
├── rag-service/
│   ├── app/
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── tests/
│   └── README.md
│
│
├── llm-service/
│   ├── app/
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── tests/
│   └── README.md
│
├── db-service/
│   ├── app/
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── tests/
│   └── README.md
│
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
│   ├── vite.config.js
│   ├── Dockerfile
│   ├── tests/
│   └── README.md
│
├── k8s/
│   ├── api-service.yaml
│   ├── rag-service.yaml
│   ├── ocr-service.yaml
│   ├── llm-service.yaml
│   ├── db-service.yaml
│   ├── frontend.yaml
│   ├── ingress.yaml
│   └── configmap.yaml
│
├── .github/
│   └── workflows/
│       └── ci-cd.yml          ← ✅ GitHub Actions CI/CD
│
├── docker-compose.yml
├── README.md
|
├── setup-service/
│   ├── requirements.txt
│   └── Dockerfile
|
└── scripts/
    └── deploy.sh
```

## System API Routes and Logic Flow

```
Frontend
   ↓
API-Service
   ├── POST /reply
   │       ↓
   │    RAG-Service (performs semantic search from Vector DB using
        query and stored vectors via Ingestion-Service)
   │       ↓
   │    LLM-Service (generates answers using LLM from the content from RAG-Service)
   │
   └── POST /upload_docs
           ↓
       Text-Parser-Service (extracts text from PDFs)
           ↓
       (If text extraction fails)
           ↓
       OCR-Service (extracts text from images/PDFs)
           ↓
       Ingestion-Service
           ↓
       Embedding & Vector Storage (stores document chunks in Vector DB)

```

## Tech Stack

| **Component**              | **Technology / Tool / Library**                                                                                                       | **Notes**                                                                         |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| **Embedding / Chunking**   | HuggingFace Embeddings (`sentence-transformers/all-MiniLM-L6-v2`) or (`all-mpnet-base-v2`) + Langchain RecursiveCharacterTextSplitter | Embedding model for semantic vectorization; text chunking with Langchain splitter |
| **Vector Database**        | Weaviate (v1.31.0 Docker container)                                                                                                   | Stores document chunks and query vectors                                          |
| **Backend Framework**      | FastAPI                                                                                                                               | API endpoints for `/reply` and other services                                     |
| **Async HTTP Client**      | `httpx.AsyncClient`                                                                                                                   | Used in main service to call RAG service                                          |
| **Message Queue**          | RabbitMQ + `aio_pika` async Python client                                                                                             | For async processing of documents and user messages                               |
| **Logging**                | `loguru`                                                                                                                              | Structured logging throughout services                                            |
| **Text Processing**        | Langchain Text Splitter                                                                                                               | RecursiveCharacterTextSplitter for chunking input text                            |
| **AI/LLM Integration**     | (Planned) LLM query module                                                                                                            | Possibly OpenAI or other LLM to generate answers (LLama2 → HuggingFace)           |
| **Containerization**       | Docker + Docker Compose                                                                                                               | Weaviate, RabbitMQ, services orchestrated via compose, Kubernetes                 |
| **Programming Language**   | Python 3.10                                                                                                                           | Core language for backend and services                                            |
| **API Client**             | `aio_pika` + `aiormq`                                                                                                                 | Async AMQP protocol for message consumption and queue management                  |
| **Environment Management** | `.env` variables (e.g. `WEAVIATE_URL`, `RABBITMQ_URL`, host urls)                                                                     | Configuration through environment                                                 |

## Service API Routes

**API Service** http://localhost:8000/docs
Perform semantic search and LLM response : http://localhost:8001/reply

Upload docs check docs format, if it's pdf use text-parser-service, else use ocr-service : http://localhost:8001/upload_docs  
(allowed_ocr_formats = [".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif"])

**Text Parser Service** http://localhost:8001/docs
Upload docs and perform ingestion by chunking, embedding and vector store : http://localhost:8001/parse

## Checking objects stored in Weaviate DB

[Open terminal paste]  
curl http://localhost:8080/v1/objects?class=DocumentChunk&limit=5  
curl http://localhost:8080/v1/objects?limit=5  
WEAVIATE STUDIO: http://localhost:8080

## RabbitMQ UI

RabbitMQ UI: http://localhost:15672/

## Sample Query

File: The Multifaceted Nature of Technological Advancements in Contemporary Society.pdf

Sample Prompt: “How have technological advancements impacted healthcare and what ethical considerations do they raise?”
