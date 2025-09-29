#text-parser-service/publisher.py

import aio_pika                      # Async RabbitMQ client
from pydantic import BaseModel       # For message schema
from loguru import logger            # For logging
import os                            # For env variables

class MessageModel(BaseModel):
    text: str
    source: str            # filename or document source
    # user_id: Optional[str] = "anonymous"  # optional user ID
    # timestamp: Optional[str] = None        # ISO timestamp

class AsyncRabbitMQPublisher:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.rabbitmq_url = os.getenv("RABBITMQ_URL")

    async def connect(self):
        self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
        self.channel = await self.connection.channel()
        logger.success("Connected to RabbitMQ")

    async def publish(self, message: MessageModel):
        if not self.connection:
            await self.connect()
        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=message.json().encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key="rag_queue"
        )
        logger.info(f"Published message: {message.json()}")

    async def close(self):
        if self.connection:
            await self.connection.close()
            self.connection = None
            self.channel = None
