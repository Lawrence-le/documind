# api-service/publisher.py

import aio_pika                      # Asynchronous RabbitMQ client
import asyncio                       # Async I/O support
from pydantic import BaseModel       # For data validation
from loguru import logger            # For logging
import os                            # For environment variable access

# Define the structure of the message using Pydantic
class MessageModel(BaseModel):
    text: str
    user_id: str
    timestamp: str = None  # Optional

# Asynchronous RabbitMQ Publisher class
class AsyncRabbitMQPublisher:
    def __init__(self):
        # Initialize connection and channel to None
        self.connection = None
        self.channel = None
        # Get RabbitMQ URL from environment variable 
        self.rabbitmq_url = os.getenv("RABBITMQ_URL")

    # Connect to RabbitMQ
    async def connect(self):
        # Establish a robust connection (auto-reconnect on failure)
        self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
        # Open a channel within the connection
        self.channel = await self.connection.channel()
        # Log success
        logger.success("Connected to RabbitMQ")

    # Publish a message to the queue
    async def publish(self, message: MessageModel):
        # Ensure connection is established
        if not self.connection:
            await self.connect()
        # Publish the message to the default exchange, routed to the specified queue
        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=message.json().encode(),                 # Encode message as JSON bytes
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT  # Ensure message is persisted to disk
            ),
            routing_key="user_message_queue"  # Route message to this queue
        )
        # Log that the message was published
        logger.info(f"Published message: {message.json()}")

    # Close the connection
    async def close(self):
        if self.connection:
            await self.connection.close()
            self.connection = None
            self.channel = None
