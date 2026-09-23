# FastAPI + RabbitMQ — Reliable Asynchronous Order Processing

## 1. Project Overview

Built an asynchronous order-processing service using **FastAPI, RabbitMQ, Python, and SQLite**.

The project demonstrates how a backend API can publish events to a message broker while a separate background consumer processes them independently. It also covers reliable messaging concepts such as publisher confirms, persistent messages, acknowledgements, retries, dead-letter queues, and idempotent database operations.

## 2. Tech Stack

- Python 3
- FastAPI
- RabbitMQ 4 Management
- `aio-pika`
- `asyncio`
- SQLite
- Pydantic
- Docker
- Uvicorn

## 3. Architecture

```text
Client
  |
  | POST /orders
  v
FastAPI Order API
  |
  | Persistent message + publisher confirmation
  v
RabbitMQ Direct Exchange
  |
  v
Durable Order Queue
  |
  v
Async Consumer
  |
  | Validate event and process order
  v
SQLite Database
  |
  +--> processed_events (deduplication)
  |
  +--> orders (business data)

Failed messages:
Order Queue --> Retry Queue --> Order Queue
Order Queue --> Dead Letter Exchange --> DLQ
```

## 4. Project Structure

```text
fastapi-rabbitmq/
├── main.py
├── consumer.py
├── database.py
├── rabbitmq_topology.py
├── test_duplicate.py
├── test_failure.py
├── orders.db
└── README.md
```

`orders.db` is generated at runtime and should not be committed to Git.

## 5. Environment Setup

### Start RabbitMQ

```bash
docker start rabbitmq
```

RabbitMQ endpoints:

- AMQP: `localhost:5672`
- Management UI: http://localhost:15672
- Default development credentials: `guest` / `guest`

### Activate the virtual environment

```bash
cd ~/suresh/microservices-demo/fastapi-rabbitmq
source ../venv/bin/activate
```

Install dependencies if needed:

```bash
pip install fastapi uvicorn aio-pika
```

## 6. FastAPI Order Service

**File:** `main.py`

Implemented:

- `GET /health` — reports service status and RabbitMQ connection state.
- `POST /orders` — validates order details and publishes an event.
- Pydantic request validation.
- Unique event IDs and order IDs.
- Persistent RabbitMQ messages.
- Publisher confirms and mandatory routing.
- RabbitMQ connection initialization and cleanup through FastAPI lifespan.

Example request:

```bash
curl -X POST http://localhost:8001/orders -H "Content-Type: application/json" -d '{"customer_id":1,"item":"Laptop","quantity":1}'
```

Expected behavior: returns HTTP `202 Accepted` after the event is published successfully. This means the order was accepted for asynchronous processing, not that the consumer has completed processing.

## 7. RabbitMQ Topology

**File:** `rabbitmq_topology.py`

Configured:

| Component | Name |
|---|---|
| Main exchange | `fastapi_orders_exchange` |
| Main queue | `fastapi_orders_queue_v2` |
| Retry exchange | `fastapi_orders_retry_exchange` |
| Retry queue | `fastapi_orders_retry_queue` |
| Dead-letter exchange | `fastapi_orders_dlx` |
| Dead-letter queue | `fastapi_orders_dlq` |
| Routing key | `order.created` |

The main queue uses dead-letter routing to forward rejected messages to the DLQ. The retry queue uses a 5-second TTL before routing the message back to the main exchange.

A separate `fastapi_orders_queue_v2` was created because RabbitMQ does not permit incompatible redeclarations of existing queue arguments.

## 8. Asynchronous Consumer

**File:** `consumer.py`

The consumer:

1. Connects to RabbitMQ.
2. Configures `prefetch_count=1`.
3. Consumes order events asynchronously.
4. Parses JSON messages.
5. Saves orders to SQLite.
6. Acknowledges successful processing.
7. Schedules retries for processing failures.
8. Sends messages to the DLQ after the retry limit.

The configured retry policy allows one initial attempt and up to three retries.

## 9. Database Persistence and Idempotency

**File:** `database.py`

Two SQLite tables are used:

### `orders`

Stores processed order information:

- `order_id`
- `customer_id`
- `item`
- `quantity`
- `status`

### `processed_events`

Stores unique event IDs to prevent repeated business processing.

The event ID is a primary key. An `INSERT OR IGNORE` operation detects duplicate events, while the order insert and event record are committed in the same database transaction.

### Duplicate-event test

**File:** `test_duplicate.py`

The producer publishes the same event ID twice:

```json
{
  "event_id": "duplicate-test-001",
  "order_id": "order-duplicate-001",
  "customer_id": 1,
  "item": "Keyboard",
  "quantity": 1
}
```

Verified database output:

```text
Duplicate-test order count: 1
Duplicate-test event count: 1
```

This confirms that repeated delivery of the same event ID does not create duplicate database records in this test.

## 10. Retry and Dead-Letter Queue

**File:** `test_failure.py`

The test producer publishes an event with `simulate_failure: true` to trigger an intentional processing error.

Expected failure flow:

```text
Initial attempt
    |
    v
Failure
    |
    v
Retry queue (5-second TTL)
    |
    v
Main queue
    |
    +--> Retry again
    |
    v
Maximum retries reached
    |
    v
Dead-letter queue
```

The configured limit is three retries after the initial attempt.

The failure producer is implemented. A complete retry/DLQ test should also verify that the message appears in `fastapi_orders_dlq` after the final failed attempt.

## 11. Health Check

Start the API:

```bash
uvicorn main:app --reload --port 8001
```

Check the health endpoint:

```bash
curl http://localhost:8001/health
```

Verified output:

```json
{
  "status": "ok",
  "rabbitmq_connected": true
}
```

This endpoint checks whether the RabbitMQ connection is marked as open. It is a basic health check, not a full readiness or end-to-end messaging test.

## 12. Verification Results

The following results were observed during the hands-on exercise:

| Test | Observed result |
|---|---|
| FastAPI startup | Successful |
| RabbitMQ connection | Successful |
| `/docs` endpoint | HTTP 200 |
| `/health` endpoint | HTTP 200 |
| `POST /orders` | HTTP 202 |
| Consumer processing | Successful |
| SQLite persistence | 4 orders present |
| Processed event records | 4 records |
| Duplicate event test | One order and one event record |
| Main v2 queue | 0 ready, 0 unacknowledged |
| Retry queue at inspection | 0 ready, 0 unacknowledged |
| DLQ failure test | Requires final verification |

The four stored orders included two Phone orders, one Keyboard duplicate-test order, and one Laptop order.

The older `fastapi_orders_queue` had five ready messages at the time of inspection. These belong to the original queue and are separate from the new `fastapi_orders_queue_v2`. They should be inspected before deciding whether to consume or remove them.

## 13. RabbitMQ Operational Commands

List queue depths:

```bash
docker exec rabbitmq rabbitmqctl list_queues name messages_ready messages_unacknowledged
```

View RabbitMQ logs:

```bash
docker logs rabbitmq
```

Compile Python files:

```bash
python -m py_compile main.py consumer.py database.py rabbitmq_topology.py test_duplicate.py test_failure.py
```

Verify SQLite contents:

```bash
python -c "import sqlite3; c=sqlite3.connect('orders.db'); print(c.execute('SELECT order_id,item,status FROM orders').fetchall()); print(c.execute('SELECT event_id FROM processed_events').fetchall()); c.close()"
```

## 14. Production Considerations

This project is a hands-on learning implementation, not a complete production deployment.

Areas for further hardening:

- Use a transactional outbox to make database writes and event publication reliably coordinated.
- Handle retry publishing failures without creating uncontrolled redelivery loops.
- Add retry backoff, poison-message handling, and DLQ alerts.
- Validate event schemas and handle malformed messages separately.
- Add structured logs, metrics, tracing, and queue-depth monitoring.
- Implement graceful shutdown and test in-flight message recovery.
- Secure RabbitMQ with dedicated users, passwords, permissions, and TLS where appropriate.
- Add integration tests for broker outages and consumer restarts.
- Use database-backed idempotency for business operations and external-service idempotency keys for operations such as payments.

## 15. Learning Outcomes

Through this project, I practiced:

- Building asynchronous APIs with FastAPI.
- Integrating Python applications with RabbitMQ.
- Publishing persistent messages with publisher confirms.
- Routing events through exchanges, queues, and routing keys.
- Implementing asynchronous consumers and manual acknowledgements.
- Persisting order data in SQLite.
- Preventing duplicate database processing through idempotency.
- Configuring delayed retries and dead-letter routing.
- Verifying queue states and application health.

## 16. Next Improvements

- Add automated tests with `pytest`.
- Add Docker Compose for the API, consumer, and RabbitMQ.
- Add structured logging and metrics.
- Integrate PostgreSQL and SQLAlchemy.
- Implement a transactional outbox.
- Add CI/CD and deployment configuration.
