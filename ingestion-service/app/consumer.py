# ingestion-service/consumer.py

import aio_pika
import asyncio
import json
from loguru import logger
import os
import signal
from langchain.text_splitter import RecursiveCharacterTextSplitter
from embedding_store import embed_and_store, ensure_schema  

RABBITMQ_URL = os.getenv("RABBITMQ_URL")

# Text Processing Logic

def clean_text(text: str) -> str:
    # Replace fancy bullets and pipes with clearer separators
    # text = text.replace("•", "•")
    # text = text.replace("-", "-")
    text = text.replace("|", "\n")  # separates inline details into rows
    return ' '.join(text.split())

def chunk_text_with_langchain(text: str, chunk_size=500, chunk_overlap=100):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "•", "-", "|", ".", " "]
    )
    return splitter.split_text(text)


# Rabbit MQ Logic

'''
connect: Establish a robust connection and channel
setup_queues: Declare rag_queue with TTL and dead-letter exchange
process_message: 
start_consuming: Consume messages by pass process_message which includes business logic
shutdown: Handles shutdown
'''
class AsyncRabbitMQConsumer:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.rag_queue = None
        self.user_message_queue = None
        self.dlq_queue = None
        self.running = True

    async def connect(self):
        # Establish a connection and channel
        self.connection = await aio_pika.connect_robust(RABBITMQ_URL)
        self.channel = await self.connection.channel()
        logger.success("Connected to RabbitMQ")

        # Ensure Weaviate schema is ready before consuming
        logger.info("Ensuring Weaviate schema exists...")
        await asyncio.to_thread(ensure_schema)  # run sync in thread

    async def setup_queues(self):

        # Declare DLX
        # dlx = await self.channel.declare_exchange("dlx", aio_pika.ExchangeType.DIRECT, durable=True)
        # dlx = await self.channel.declare_exchange("dlx", aio_pika.ExchangeType.FANOUT, durable=True)

        # Declare DLQ and bind to DLX
        # dlq_queue = await self.channel.declare_queue("dlq", durable=True)
        # await dlq_queue.bind(dlx, routing_key="dlq")

        # Declare rag_queue
        self.rag_queue = await self.channel.declare_queue(
            "rag_queue",
            durable=True,
            arguments={
                "x-message-ttl": 60000,
                "x-dead-letter-exchange": "dlx",
            }
        )

        # Declare user_message_queue
        self.user_message_queue = await self.channel.declare_queue(
            "user_message_queue",
            durable=True,
            arguments={
                "x-message-ttl": 60000,
                "x-dead-letter-exchange": "dlx",
            }
        )

        logger.info("Queues and DLX/DLQ set up")

    async def process_doc_message(self, message: aio_pika.IncomingMessage):
        async with message.process():
            body = message.body.decode()
            data = json.loads(body)
            logger.success("Received document from text-parser")

            cleaned_text = clean_text(data["text"])
            chunks = chunk_text_with_langchain(cleaned_text)
            logger.info(f"Total chunks created: {len(chunks)}")

            for i, chunk in enumerate(chunks[:2]):
                logger.debug(f"Chunk {i + 1}: {chunk}")

            await embed_and_store(chunks)

    async def process_user_message(self, message: aio_pika.IncomingMessage):
        async with message.process():
            body = message.body.decode()
            data = json.loads(body)
            logger.success(f"Received user message: {data}")
            logger.info(f"User message received: {data['text']}")

    async def start_consuming(self):
        await self.rag_queue.consume(self.process_doc_message)
        await self.user_message_queue.consume(self.process_user_message)
        # await self.dlq_queue.consume(self.process_dlq_message)
        logger.info("Started consuming rag_queue and user_message_queue")

    async def shutdown(self):
        self.running = False
        logger.info("Shutting down consumer...")

        if self.connection:
            await self.connection.close()
            logger.success("RabbitMQ connection closed")

    async def run(self):
        await self.connect()
        await self.setup_queues()
        await self.start_consuming()

        # Wait until shutdown is triggered (signal or manual stop)
        while self.running:
            await asyncio.sleep(1)

# Global consumer instance
consumer = AsyncRabbitMQConsumer()

# Graceful shutdown on SIGINT / SIGTERM
def handle_signal(sig_num, frame):
    logger.warning(f"Received signal {sig_num}, triggering shutdown...")
    asyncio.create_task(consumer.shutdown())

signal.signal(signal.SIGINT, handle_signal) # Ctrl+C
signal.signal(signal.SIGTERM, handle_signal) # kill or Docker stop

if __name__ == "__main__":
    try:
        asyncio.run(consumer.run())
    except KeyboardInterrupt:
        logger.warning("Keyboard interrupt received, exiting...")

