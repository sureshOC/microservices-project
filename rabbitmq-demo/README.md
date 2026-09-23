# RabbitMQ Hands-On Learning — Python & Async Messaging

## Overview

This repository contains hands-on experiments for learning RabbitMQ messaging patterns using Python, `aio-pika`, Docker, and asynchronous programming.

The goal is to understand how messaging systems work in real-world backend and microservices architectures, including message routing, reliable delivery, failure recovery, retries, and duplicate-message handling.

## Tech Stack

- Python 3
- RabbitMQ 4 with Management UI
- Docker
- `aio-pika`
- `asyncio`
- SQLite

## Environment Setup

### 1. Start RabbitMQ using Docker

```bash
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:4-management
```

If the container already exists, start it using:

```bash
docker start rabbitmq
```

### 2. Access RabbitMQ Management UI

Open http://localhost:15672

Default development credentials:

- Username: `guest`
- Password: `guest`

### 3. Set up Python environment

```bash
python3 -m venv ../venv
source ../venv/bin/activate
pip install aio-pika
```

## Topics Covered

### 1. Producer and Consumer Basics

**Files:** `producer.py`, `consumer.py`

Learned how to publish messages to RabbitMQ and consume them asynchronously.

Key concepts:
- Establishing RabbitMQ connections using `aio_pika.connect_robust()`.
- Creating channels and declaring queues.
- Publishing messages through the default exchange.
- Consuming messages using queue iterators.
- Using `async` and `await` for asynchronous I/O.

### 2. Message Acknowledgements — ACK and NACK

Learned how RabbitMQ tracks message-processing outcomes.

- **ACK:** Confirms successful processing and removes the message from the queue.
- **NACK with requeue:** Rejects the message and requests redelivery.
- **NACK without requeue:** Rejects the message without retrying it in the same queue; dead-letter routing can send it to a DLQ.
- **Unacknowledged messages:** Messages delivered to a consumer but not yet acknowledged.
- **`message.process()`:** Provides automatic acknowledgement on successful completion and rejection on exceptions, depending on its configuration.

### 3. Direct Exchange and Routing Keys

**Files:** `direct_producer.py`, `multi_producer.py`

Learned how direct exchanges route messages using exact routing-key matches.

Example routing keys:
- `order.created`
- `payments.created`

Key takeaway: multiple queues can bind to the same routing key. Each matching queue receives a copy of the published message.

### 4. Fanout Exchange

**File:** `fanout_demo.py`

Learned how fanout exchanges broadcast messages to every queue bound to the exchange.

Example use cases:
- Notifications
- Audit events
- Event broadcasting

The routing key is ignored by a fanout exchange.

### 5. Topic Exchange

**File:** `topic_demo.py`

Learned pattern-based routing using wildcards.

- `order.*` matches exactly one word after `order`.
- `order.#` matches zero or more words after `order`.

Example:
- `order.created`
- `order.cancelled`
- `order.payment.completed`

Topic exchanges are useful when multiple services need different categories of events.

### 6. Competing Consumers and Prefetch

**Files:** `worker_producer.py`, `worker.py`

Learned how multiple workers consume messages from a shared queue.

Key concepts:
- Work distribution among consumers.
- Processing time and consumer throughput.
- `channel.set_qos(prefetch_count=1)`.
- How acknowledgements release prefetch capacity.

With prefetch set to one, a consumer generally receives no additional messages while it has one unacknowledged delivery. This can improve distribution when workers have different processing speeds.

### 7. Dead-Letter Queue (DLQ)

**Files:** `dlq_setup.py`, `dlq_producer.py`, `dlq_consumer.py`

Implemented a dead-letter exchange and dead-letter queue.

Flow:

`orders_exchange → orders_queue → orders_dlx → orders_dlq`

Learned:
- Configuring `x-dead-letter-exchange`.
- Configuring `x-dead-letter-routing-key`.
- Rejecting messages without requeue.
- Inspecting failed messages in RabbitMQ Management UI.
- Why queue declarations must use compatible arguments.

**Important:** RabbitMQ rejects incompatible redeclarations of an existing queue. The queue's durability and arguments must match its original declaration.

### 8. Retry Mechanism with TTL and DLQ

**Files:** `retry_setup.py`, `retry_producer.py`, `retry_consumer.py`

Implemented delayed retries using a retry queue with a 5-second message TTL.

Flow:

`orders_exchange → orders_queue → orders_retry_queue → orders_exchange`

After the retry limit is reached:

`orders_queue → orders_dlx → orders_dlq`

Key concepts:
- Message TTL using `x-message-ttl`.
- Retry counts stored in message headers.
- Retry routing through a dedicated exchange.
- Moving permanently failed messages to a DLQ.

With `MAX_RETRIES = 3`, the demo allows one initial attempt plus up to three retries: four processing attempts in total.

**Production consideration:** Republishing a message and then acknowledging the original can result in duplicates if the consumer crashes between those operations. Publisher confirms, idempotency, and reliable retry designs are important.

### 9. Publisher Confirms and Persistent Messages

**File:** `confirm_producer.py`

Learned how publishers can verify that RabbitMQ has accepted published messages.

Key concepts:
- `publisher_confirms=True`
- `mandatory=True`
- `on_return_raises=True`
- `DeliveryMode.PERSISTENT`
- Durable exchanges and queues

A successful publisher confirmation indicates broker acceptance. An unroutable mandatory message can raise a `PublishError` with `NO_ROUTE`.

**Important distinction:** Publisher confirms do not mean that a consumer has processed the message. Durable queues, persistent messages, and publisher confirms improve reliability but do not guarantee protection against every possible infrastructure failure.

### 10. Idempotent Consumers

**Files:** `idempotency_producer.py`, `idempotency_consumer.py`

Implemented duplicate-message protection using SQLite.

The producer publishes the same event twice with the same event ID:

```json
{
  "event_id": "evt-8001",
  "order_id": 8001,
  "amount": 100
}
```

The consumer records each event in a database table with a unique primary key.

```sql
CREATE TABLE processed_events (
    event_id TEXT PRIMARY KEY,
    processed_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

Expected consumer output:

```text
Idempotency consumer is waiting for messages...
Order processed: 8001 | Event: evt-8001
Duplicate event skipped: evt-8001
```

Database verification:

```bash
python -c "import sqlite3; c=sqlite3.connect('rabbitmq_idempotency.db'); print(c.execute('SELECT * FROM processed_events').fetchall()); print(c.execute('SELECT * FROM orders').fetchall()); c.close()"
```

Expected result: one processed event and one order with `processing_count = 1`.

**Key takeaway:** RabbitMQ may redeliver messages. Idempotency prevents repeated business effects when the same event is delivered multiple times.

For database-backed processing, the deduplication record and business changes should be committed in the same transaction.

## Important RabbitMQ Concepts

| Concept | Purpose |
|---|---|
| Producer | Publishes messages |
| Consumer | Receives and processes messages |
| Queue | Stores messages until delivery |
| Exchange | Routes messages to queues |
| Routing key | Determines routing for direct and topic exchanges |
| ACK | Confirms successful processing |
| NACK | Rejects a delivery |
| Prefetch | Limits outstanding unacknowledged deliveries |
| TTL | Controls message lifetime |
| DLQ | Stores dead-lettered messages |
| Publisher confirms | Confirms broker acceptance |
| Persistent message | Requests message persistence |
| Idempotency | Prevents duplicate business operations |

## RabbitMQ Commands

Check the container:

```bash
docker ps
```

View RabbitMQ logs:

```bash
docker logs rabbitmq
```

Stop RabbitMQ:

```bash
docker stop rabbitmq
```

Start RabbitMQ again:

```bash
docker start rabbitmq
```

Check Python syntax:

```bash
python -m py_compile idempotency_consumer.py
```

## Practical Lessons Learned

1. RabbitMQ supports asynchronous communication between services.
2. Exchanges determine how messages are routed to queues.
3. ACK and NACK control message-delivery outcomes.
4. Prefetch affects how messages are distributed to consumers.
5. DLQs help isolate failed messages for investigation.
6. TTL-based retry queues can implement delayed retries.
7. Publisher confirms improve publisher-side reliability.
8. Idempotent consumers protect business operations from duplicate deliveries.
9. Durable queues and persistent messages help preserve messages across broker restarts, subject to the broker's storage and failure guarantees.
10. Production systems also need monitoring, connection recovery, graceful shutdown, error handling, and safe database transactions.

## Next Step: FastAPI + RabbitMQ Integration

The next hands-on project will integrate RabbitMQ into a FastAPI microservices workflow.

Planned flow:

`Client → FastAPI Order API → RabbitMQ → Background Consumer → Database`

Objectives:
- Publish `OrderCreated` events from a FastAPI endpoint.
- Process orders asynchronously in a separate consumer.
- Implement retries and dead-letter handling.
- Make database processing idempotent.
- Test failure scenarios and message recovery.
- Add logging and health checks.

## Learning Outcome

After completing these exercises, I understand the fundamentals of RabbitMQ exchanges, queues, routing, asynchronous consumers, acknowledgements, competing workers, retry mechanisms, dead-letter queues, publisher confirms, persistent messages, and idempotent processing.

This foundation will be used to build reliable asynchronous communication into Python backend and microservices applications.

