FROM python:3.10-slim

WORKDIR /app

COPY setup-service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy scripts folder from project root
COPY scripts/rabbitmq_setup.py .

CMD ["python", "rabbitmq_setup.py"]