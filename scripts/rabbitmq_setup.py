# rabbitmq_setup.py

import asyncio
import aio_pika
import os
from loguru import logger

RABBITMQ_URL = os.getenv("RABBITMQ_URL")

async def setup_rabbitmq():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()

    # Declare Dead Letter Exchange and Queue
    exchange = await channel.declare_exchange("dlx", aio_pika.ExchangeType.FANOUT, durable=True)
    
    # Declare Dead Letter Queue
    queue = await channel.declare_queue("dlq", durable=True)
    
    # Bind queue to exchange
    await queue.bind(exchange)

    # Declare Main Queue with TTL and DLX
    await channel.declare_queue(
        "rag_queue",
        durable=True,
        arguments={
            "x-message-ttl": 60000,  # Message expires in 60s and goes to the dlx
            "x-dead-letter-exchange": "dlx",  # Unprocessed messages go here
        },
    )

    logger.success("RabbitMQ setup completed.")

    await connection.close()

if __name__ == "__main__":
    asyncio.run(setup_rabbitmq())
