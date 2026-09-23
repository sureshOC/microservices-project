import json
import uuid
from contextlib import asynccontextmanager
import aio_pika
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from rabbitmq_topology import setup_topology

RABBITMQ_URL = "amqp://guest:guest@localhost/"
connection = None
channel = None
exchange = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global connection, channel, exchange
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel(publisher_confirms=True, on_return_raises=True)
    exchange, _ = await setup_topology(channel)
    print("Connected to RabbitMQ; topology declared")
    try:
        yield
    finally:
        await connection.close()
        print("RabbitMQ connection closed")

app = FastAPI(title="Reliable Order Service", lifespan=lifespan)

class OrderRequest(BaseModel):
    customer_id: int = Field(gt=0)
    item: str = Field(min_length=1, max_length=100)
    quantity: int = Field(gt=0)

@app.get("/health")
async def health():
    connected = connection is not None and not connection.is_closed
    return {"status": "ok" if connected else "unavailable", "rabbitmq_connected": connected}

@app.post("/orders", status_code=202)
async def create_order(order: OrderRequest):
    if exchange is None:
        raise HTTPException(status_code=503, detail="RabbitMQ unavailable")
    event = {"event_id": str(uuid.uuid4()), "order_id": str(uuid.uuid4()), **order.model_dump()}
    message = aio_pika.Message(body=json.dumps(event).encode(), content_type="application/json", delivery_mode=aio_pika.DeliveryMode.PERSISTENT, message_id=event["event_id"])
    try:
        await exchange.publish(message, routing_key="order.created", mandatory=True)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Could not publish order event") from exc
    return {"message": "Order accepted for asynchronous processing", "event": event}
