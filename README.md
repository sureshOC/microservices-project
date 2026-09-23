# Production-Style Python Microservices

A hands-on, production-oriented microservices project built with **Python, FastAPI, PostgreSQL, Redis, and asynchronous communication**.

The purpose of this project is not only to build APIs, but to understand how distributed backend services behave under **timeouts, failures, retries, concurrency, duplicate requests, caching, stale data, cache stampede, and dependency outages**.

> **Learning approach:** Reproduce the problem → understand why it happens → implement a solution → test it under concurrency/failure → understand the trade-offs → explain it in an interview.

---

# 1. Project Goals

This project is designed to build practical knowledge of:

- Python backend development
- FastAPI
- Microservices architecture
- REST communication
- Async programming
- Service-to-service communication
- Resilience patterns
- Retry and exponential backoff
- Circuit breaker
- Idempotency
- Database concurrency
- PostgreSQL
- SQLAlchemy
- Redis caching
- Cache invalidation
- TTL
- Cache stampede protection
- Failure handling
- RabbitMQ / event-driven architecture
- API Gateway
- Observability
- Docker
- Kubernetes

---

# 2. Current Architecture

```text
                         Client
                           |
                           |
                    API Gateway
                    (Planned)
                           |
          +----------------+----------------+
          |                |                |
          v                v                v
    User Service     Order Service    Product Service
      :8001             :8002              :8004
                           |
                           |
                           v
                    Payment Service
                       :8003
                           |
                           v
                     PostgreSQL


             Product Service
                  |
                  v
                Redis
                 Cache


              RabbitMQ
             (Planned)
                  |
       +----------+----------+
       |          |          |
       v          v          v
   Payment    Inventory   Notification
   Service     Service      Service
```

---

# 3. Services

## 3.1 User Service

**Port:** `8001`

Responsibilities:

- User lookup
- User APIs
- Acts as a downstream dependency for Order Service
- Used to demonstrate timeout, retry, and circuit breaker behavior

Example:

```http
GET /users/{user_id}
```

---

## 3.2 Order Service

**Port:** `8002`

Responsibilities:

- Order APIs
- Service-to-service communication
- Calls User Service
- Timeout handling
- Retry with exponential backoff
- Circuit breaker

Example flow:

```text
Client
  |
  v
Order Service
  |
  v
User Service
```

---

## 3.3 Payment Service

**Port:** `8003`

Responsibilities:

- Payment processing
- Idempotency
- Duplicate request protection
- PostgreSQL persistence
- Transaction/concurrency handling

Example concept:

```text
Client
  |
  | idempotency-key
  v
Payment Service
  |
  v
PostgreSQL
```

---

## 3.4 Product Service

**Port:** `8004`

Responsibilities:

- Product retrieval
- Product update
- Redis cache
- Cache-aside pattern
- TTL
- Cache invalidation
- Cache stampede protection
- Redis failure handling

Example:

```http
GET /products/{product_id}
PUT /products/{product_id}
```

---

# 4. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend development |
| FastAPI | REST API framework |
| Uvicorn | ASGI server |
| HTTPX | Async HTTP client |
| PostgreSQL | Persistent database |
| SQLAlchemy | ORM |
| Redis | Caching |
| RabbitMQ | Async messaging - planned |
| Docker | Containerization - planned |
| Nginx | API Gateway / reverse proxy - planned |
| Pytest | Testing |
| Prometheus | Metrics - planned |
| Grafana | Monitoring - planned |
| OpenTelemetry | Distributed tracing - planned |
| Kubernetes | Container orchestration - planned |

---

# 5. Microservices Concepts Implemented

## 5.1 Service-to-Service Communication

Order Service communicates with User Service over HTTP.

```text
Order Service
      |
      | HTTP
      v
User Service
```

Using:

```python
httpx.AsyncClient
```

### Important point

In microservices, a downstream service can be:

- slow
- unavailable
- returning errors
- overloaded
- temporarily unreachable

Therefore every service call needs appropriate timeout and failure handling.

---

# 6. Timeout Handling

A downstream service should never be allowed to block the caller indefinitely.

Example:

```text
Order Service
      |
      | request
      v
User Service
      |
      | slow response
      v
Timeout
```

Example:

```python
async with httpx.AsyncClient(timeout=3.0) as client:
    response = await client.get(url)
```

### Why timeout matters

Without a timeout:

```text
Slow dependency
      ↓
Request waits
      ↓
More requests wait
      ↓
Connections get exhausted
      ↓
Service becomes unhealthy
```

### Interview answer

> I set explicit timeouts for downstream calls so a slow dependency cannot consume resources indefinitely.

---

# 7. Retry with Exponential Backoff

Transient failures can sometimes recover if we retry.

Example:

```text
Attempt 1
   ↓
Failure
   ↓
wait 1 sec
   ↓
Attempt 2
   ↓
Failure
   ↓
wait 2 sec
   ↓
Attempt 3
   ↓
Failure
   ↓
wait 4 sec
```

Formula:

```python
delay = 2 ** (attempt - 1)
```

Example delays:

```text
1 → 2 → 4 → 8
```

### Important

Do not blindly retry every HTTP error.

Generally:

```text
4xx
→ usually do not retry

5xx
→ depends on the operation

Timeout / connection failure
→ may be retryable
```

Retries should also have:

- maximum attempts
- timeout
- backoff
- preferably jitter in production

### Why?

Too many retries can create a:

```text
Retry Storm
```

where an already failing dependency receives even more traffic.

### Interview answer

> I use bounded retries with exponential backoff for transient failures, while avoiding retries for permanent client errors such as most 4xx responses.

---

# 8. Circuit Breaker

A circuit breaker protects a service when a dependency is repeatedly failing.

States:

```text
             failures exceed threshold
 CLOSED ------------------------------> OPEN
    ^                                     |
    |                                     |
    | success                             | recovery timeout
    |                                     |
    +-------------------------------- HALF_OPEN
```

## CLOSED

Normal traffic.

```text
Order → User
```

## OPEN

Dependency is considered unhealthy.

```text
Order
  |
  X
User Service
```

The request fails fast instead of calling the unhealthy dependency.

## HALF_OPEN

After a recovery period, allow a test request.

If successful:

```text
HALF_OPEN → CLOSED
```

If it fails:

```text
HALF_OPEN → OPEN
```

### Interview answer

> A circuit breaker prevents repeated calls to a failing dependency. It usually has CLOSED, OPEN, and HALF_OPEN states and allows recovery without continuously adding load to the failed service.

---

# 9. Idempotency

Idempotency is especially important for payment APIs.

Suppose the client sends:

```text
POST /payments
idempotency-key: payment-123
```

Network failure happens after the payment is processed.

The client retries:

```text
POST /payments
idempotency-key: payment-123
```

Without idempotency:

```text
Payment 1 → ₹75,000
Payment 2 → ₹75,000
```

The customer may be charged twice.

With idempotency:

```text
Request 1
   ↓
Process payment
   ↓
Save result

Request 2
   ↓
Same idempotency key
   ↓
Return existing result
```

### Key principle

```text
Same idempotency key
        +
Same logical operation
        =
Do not perform the operation twice
```

---

# 10. Race Condition in Payment Processing

A naive implementation:

```python
if key not in payments:
    process_payment()
```

looks correct but is not atomic.

Two requests can execute:

```text
Request 1 → check → key not found
Request 2 → check → key not found

Request 1 → process
Request 2 → process
```

Result:

```text
Duplicate payment
```

This was intentionally reproduced with concurrent requests.

---

# 11. asyncio.Lock

For a single Python process, an `asyncio.Lock` can protect a critical section.

Example:

```python
async with payment_lock:
    ...
```

This ensures only one coroutine enters the protected section at a time.

### Important limitation

`asyncio.Lock` is:

```text
PROCESS LOCAL
```

If there are multiple service instances:

```text
Payment Instance 1 → Lock A
Payment Instance 2 → Lock B
Payment Instance 3 → Lock C
```

The locks do not coordinate with each other.

Therefore an in-memory lock alone is not sufficient for distributed payment idempotency.

---

# 12. PostgreSQL Idempotency

The production-style solution uses a database constraint.

Example:

```sql
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    idempotency_key VARCHAR(255) UNIQUE NOT NULL,
    order_id INTEGER NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR(50) NOT NULL
);
```

Important:

```sql
UNIQUE(idempotency_key)
```

The database becomes the final concurrency protection.

If concurrent requests try to insert the same key:

```text
Request 1 → INSERT → success
Request 2 → INSERT → UNIQUE violation
Request 3 → INSERT → UNIQUE violation
```

The application catches the conflict, rolls back, and returns the existing payment result.

### Interview answer

> I don't rely only on an in-memory lock for distributed idempotency. I use a database-level unique constraint and transaction handling so the guarantee remains valid across multiple service instances.

---

# 13. Redis Cache-Aside Pattern

Product Service uses Redis as a cache.

Basic flow:

```text
Request
   |
   v
Redis
   |
   +---- HIT ----> Return cached data
   |
   +---- MISS
          |
          v
       Source/DB
          |
          v
        Redis
          |
          v
       Response
```

Example key:

```text
product:101
```

### Cache HIT

```text
Request
   ↓
Redis HIT
   ↓
Return response
```

### Cache MISS

```text
Request
   ↓
Redis MISS
   ↓
Read source
   ↓
Store Redis
   ↓
Return response
```

### Interview answer

> I use the cache-aside pattern: read Redis first, fetch from the source on a miss, populate Redis, and return the data.

---

# 14. Redis TTL

Cached data should not live forever.

Example:

```python
await redis_client.set(
    cache_key,
    json.dumps(product),
    ex=30
)
```

`ex=30` means:

```text
30 seconds
```

Redis automatically expires the key.

Check TTL:

```bash
redis-cli TTL product:101
```

Possible values:

```text
15
10
5
0
-2
```

Meaning:

```text
positive number
→ seconds remaining

-2
→ key does not exist
```

### Important limitation

TTL provides eventual expiration.

It does not guarantee immediate consistency.

---

# 15. Stale Cache

Example:

```text
Source:
price = 15000

Redis:
price = 1500
```

If the source is updated but Redis is not invalidated, users can receive stale data.

This was intentionally reproduced in the project.

---

# 16. Cache Invalidation

When product data changes:

```text
PUT /products/101
        |
        v
Update source
        |
        v
DELETE product:101 from Redis
```

Next GET:

```text
Redis MISS
   ↓
Source
   ↓
Redis SET
   ↓
Return updated data
```

Example:

```python
await redis_client.delete(
    f"product:{product_id}"
)
```

### Important interview point

> Cache invalidation ensures a write does not leave an old cached value available after the source data changes.

---

# 17. Cache Stampede / Thundering Herd

A cache stampede happens when many requests encounter the same cache miss simultaneously.

Example:

```text
Redis key expires
       |
       v
10 concurrent requests
       |
       +---- MISS → DB
       +---- MISS → DB
       +---- MISS → DB
       +---- MISS → DB
       ...
       +---- MISS → DB
```

Result:

```text
10 requests
10 database calls
```

At large scale:

```text
10,000 requests
10,000 database calls
```

This can overload the database.

---

# 18. Per-Key Lock for Cache Stampede

A per-key lock protects the expensive source load.

Example:

```python
product_locks = {}
```

Conceptually:

```text
product:101 → Lock A
product:102 → Lock B
product:103 → Lock C
```

For 10 requests for product 101:

```text
10 requests
     |
     v
Lock for product 101
     |
     +---- Request 1 → Source/DB
     |
     +---- Request 2 → Redis HIT
     |
     +---- Request 3 → Redis HIT
     |
     +---- Request 4 → Redis HIT
     |
     ...
```

Result:

```text
10 requests
     ↓
1 source call
     ↓
Redis populated
     ↓
remaining requests get cache HIT
```

### Why check Redis twice?

First check:

```python
cached_product = await redis_client.get(cache_key)
```

If miss:

```python
async with lock:
```

Then check Redis again.

Why?

Because another request may have populated Redis while this request was waiting for the lock.

```text
Request 1
   ↓
gets lock
   ↓
DB
   ↓
Redis SET
   ↓
unlock

Request 2
   ↓
gets lock
   ↓
Redis CHECK AGAIN
   ↓
HIT
```

Without the second check, Request 2 would unnecessarily call the source again.

### Interview answer

> I use a per-key lock so concurrent requests for the same cache key don't all hit the database. After acquiring the lock, I re-check Redis because another request may have populated the cache while I was waiting.

---

# 19. Redis Failure Handling

Redis is a cache, not the source of truth.

Therefore the Product Service should ideally continue working if Redis goes down.

Without handling:

```text
Redis DOWN
   ↓
Redis GET exception
   ↓
500 Internal Server Error
```

With fail-open behavior:

```text
Redis DOWN
   ↓
Redis GET fails
   ↓
Log error
   ↓
Ignore cache
   ↓
Read source/DB
   ↓
Return response
```

Example:

```python
try:
    cached_product = await redis_client.get(cache_key)
except RedisError as e:
    print(f"REDIS UNAVAILABLE → {e}")
    cached_product = None
```

Similarly, Redis SET failures should not necessarily fail the request:

```python
try:
    await redis_client.set(...)
except RedisError as e:
    print(f"REDIS SET FAILED → {e}")
```

### Design principle

```text
Database = Source of Truth
Redis = Performance Optimization
```

Therefore cache failure should normally degrade performance rather than make the whole API unavailable.

---

# 20. Current Failure Scenarios Reproduced

This project has intentionally reproduced the following:

```text
✓ Slow downstream service
✓ Downstream timeout
✓ Connection failure
✓ Retry
✓ Exponential backoff
✓ Retry exhaustion
✓ Circuit breaker OPEN
✓ Circuit breaker HALF_OPEN
✓ Circuit breaker recovery
✓ Duplicate payment requests
✓ Concurrent payment requests
✓ Race condition
✓ Database uniqueness protection
✓ Redis cache miss
✓ Redis cache hit
✓ Stale cache
✓ Redis TTL expiration
✓ Explicit cache invalidation
✓ Cache stampede
✓ Per-key cache locking
✓ Redis outage
✓ Cache fail-open behavior
```

---

# 21. Useful Commands

## Start Redis

```bash
redis-server
```

Check:

```bash
redis-cli ping
```

Expected:

```text
PONG
```

---

## Inspect Redis

```bash
redis-cli
```

List keys during local development:

```redis
KEYS *
```

Get product:

```redis
GET product:101
```

Check TTL:

```redis
TTL product:101
```

Delete key:

```redis
DEL product:101
```

---

# 22. Running the Services

## Create virtual environment

```bash
python3 -m venv venv
```

Activate:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## User Service

```bash
cd user-service
uvicorn main:app --reload --port 8001
```

---

## Order Service

```bash
cd order-service
uvicorn main:app --reload --port 8002
```

---

## Payment Service

```bash
cd payment-service
uvicorn main:app --reload --port 8003
```

---

## Product Service

```bash
cd product-service
uvicorn main:app --reload --port 8004
```

---

# 23. PostgreSQL

Create database:

```sql
CREATE DATABASE microservices;
```

Example connection string:

```text
postgresql://postgres:password@localhost:5432/microservices
```

Payment table:

```sql
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    idempotency_key VARCHAR(255) UNIQUE NOT NULL,
    order_id INTEGER NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR(50) NOT NULL
);
```

Useful PostgreSQL commands:

```sql
\l
```

List databases.

```sql
\c microservices
```

Connect to database.

```sql
\dt
```

List tables.

```sql
\d payments
```

Describe table.

```sql
SELECT * FROM payments;
```

---

# 24. Project Structure

Recommended structure:

```text
microservices/
│
├── user-service/
│   ├── main.py
│   └── ...
│
├── order-service/
│   ├── main.py
│   ├── circuit_breaker.py
│   └── ...
│
├── payment-service/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   └── ...
│
├── product-service/
│   ├── main.py
│   └── ...
│
├── tests/
│   ├── test_payment.py
│   ├── test_product.py
│   └── ...
│
├── requirements.txt
├── docker-compose.yml
└── README.md
```

---

# 25. Testing Strategy

The project uses both normal functional testing and failure testing.

## Functional testing

Example:

```text
GET product
POST payment
PUT product
GET user
```

## Failure testing

Example:

```text
Stop User Service
Stop Redis
Add downstream delay
Send duplicate payment
Send concurrent requests
Expire Redis key
Invalidate Redis key
```

## Concurrency testing

Example:

```python
tasks = [
    get_product(client, i)
    for i in range(1, 11)
]

await asyncio.gather(*tasks)
```

This helps reproduce race conditions and cache stampedes.

---

# 26. Important Production Lessons

## Lesson 1 — Every dependency can fail

Do not assume:

```text
Service A → Service B
```

will always work.

Consider:

- timeout
- connection error
- HTTP error
- slow response
- service restart

---

## Lesson 2 — Retry carefully

Retrying can help transient failures.

But:

```text
Failure
+
Unlimited retry
=
Retry storm
```

Use:

```text
bounded retries
+
backoff
+
timeouts
```

---

## Lesson 3 — Idempotency is critical

Especially for:

- payments
- orders
- message consumers
- external API calls

---

## Lesson 4 — Locks are not automatically distributed

```text
asyncio.Lock
```

only coordinates coroutines within the same process.

Multiple service instances require shared coordination or database-level guarantees where appropriate.

---

## Lesson 5 — Redis is usually not the source of truth

If Redis disappears:

```text
Redis DOWN
```

the application should normally be able to recover data from the source.

---

## Lesson 6 — Cache invalidation matters

Caching improves performance but introduces consistency problems.

Always think about:

```text
When is cache populated?
When does it expire?
When is it invalidated?
What happens if invalidation fails?
```

---

## Lesson 7 — Concurrency changes everything

Code that works for:

```text
1 request
```

may fail for:

```text
100 concurrent requests
```

Always consider race conditions and shared state.

---

# 27. Interview Revision Cheat Sheet

## Timeout

**Question:** Why use timeout?

**Answer:**

> To prevent a slow downstream dependency from blocking resources indefinitely and causing cascading failures.

---

## Retry

**Question:** How do you implement retry?

**Answer:**

> Use bounded retries with exponential backoff for transient failures, while avoiding retries for permanent errors such as most 4xx responses.

---

## Circuit Breaker

**Question:** Why circuit breaker?

**Answer:**

> To stop repeatedly calling an unhealthy dependency and allow the system to fail fast while the dependency recovers.

States:

```text
CLOSED → OPEN → HALF_OPEN → CLOSED
```

---

## Idempotency

**Question:** Why is payment idempotency important?

**Answer:**

> Network retries can cause the same payment request to be submitted multiple times. An idempotency key lets the service recognize duplicate operations and return the existing result instead of processing the payment again.

---

## Redis Cache

**Question:** Which caching pattern did you use?

**Answer:**

> Cache-aside. I check Redis first, fetch from the source on a miss, populate Redis, and return the data.

---

## TTL

**Question:** Why TTL?

**Answer:**

> TTL automatically expires cached data and limits how long stale data can remain in the cache.

---

## Cache Invalidation

**Question:** Why invalidate cache after update?

**Answer:**

> Because updating the source without invalidating the cached value can cause users to receive stale data.

---

## Cache Stampede

**Question:** What is cache stampede?

**Answer:**

> When many concurrent requests see the same cache miss and all hit the database simultaneously, potentially overwhelming the database.

---

## Per-Key Lock

**Question:** How did you solve cache stampede?

**Answer:**

> I used a per-key asyncio lock. Requests for the same product share a lock, while different products use different locks. After acquiring the lock, the request re-checks Redis so only one request loads the source.

---

## Redis Failure

**Question:** What happens if Redis goes down?

**Answer:**

> Redis is treated as a cache, so the service fails open: it logs the Redis error, bypasses the cache, and reads from the source of truth rather than returning a 500 just because the cache is unavailable.

---

# 28. What Is Implemented vs Planned

## Implemented

- [x] User Service
- [x] Order Service
- [x] Payment Service
- [x] Product Service
- [x] REST service-to-service communication
- [x] Async HTTP communication
- [x] Timeout handling
- [x] Retry
- [x] Exponential backoff
- [x] Circuit breaker
- [x] Payment idempotency
- [x] PostgreSQL persistence
- [x] Database unique constraint
- [x] Redis cache-aside
- [x] Cache hit/miss
- [x] TTL
- [x] Cache invalidation
- [x] Cache stampede reproduction
- [x] Per-key locking
- [x] Redis failure handling
- [x] Cache fail-open behavior

## Planned

- [ ] RabbitMQ
- [ ] Producer / Consumer
- [ ] Exchanges and routing
- [ ] Message acknowledgement
- [ ] Retry queues
- [ ] Dead Letter Queue
- [ ] Idempotent consumers
- [ ] Event-driven order flow
- [ ] Nginx API Gateway
- [ ] Rate limiting
- [ ] Correlation IDs
- [ ] Centralized logging
- [ ] Docker
- [ ] Docker Compose
- [ ] Product PostgreSQL database
- [ ] Prometheus
- [ ] Grafana
- [ ] OpenTelemetry
- [ ] Distributed tracing
- [ ] Kubernetes
- [ ] Kubernetes Services
- [ ] ConfigMaps
- [ ] Secrets
- [ ] Liveness probes
- [ ] Readiness probes
- [ ] Horizontal Pod Autoscaling
- [ ] CI/CD
- [ ] Integration tests
- [ ] Load testing

---

# 29. Final Target Architecture

The final target architecture is:

```text
                           Client
                              |
                              v
                       Nginx / Gateway
                              |
            +-----------------+-----------------+
            |                 |                 |
            v                 v                 v
      User Service      Order Service      Product Service
         :8001             :8002               :8004
                              |                   |
                              |                   v
                              |                 Redis
                              |
                              v
                          RabbitMQ
                     /        |        \
                    /         |         \
                   v          v          v
             Payment      Inventory   Notification
             Service       Service      Service
               :8003
                 |
                 v
             PostgreSQL


        +---------------------------------------+
        |          Observability                |
        | Prometheus | Grafana | OpenTelemetry |
        +---------------------------------------+

                    Kubernetes
                       |
          +------------+------------+
          |            |            |
       Pods/Deployments/Services/Ingress
```

---

# 30. Learning Roadmap

```text
PHASE 1 — Microservices Fundamentals
-------------------------------------
✓ REST
✓ Service-to-service communication
✓ Async HTTP
✓ Timeout
✓ Retry
✓ Exponential backoff
✓ Circuit breaker
✓ Idempotency


PHASE 2 — Caching
------------------
✓ Redis
✓ Cache-aside
✓ Cache hit/miss
✓ TTL
✓ Stale cache
✓ Cache invalidation
✓ Cache stampede
✓ Per-key locking
✓ Redis failure handling


PHASE 3 — Messaging
-------------------
□ RabbitMQ
□ Producer
□ Consumer
□ Exchange
□ Queue
□ Routing key
□ Acknowledgement
□ Retry
□ DLQ
□ Idempotent consumer


PHASE 4 — Gateway & Operations
------------------------------
□ Nginx
□ API Gateway
□ Rate limiting
□ Correlation ID
□ Centralized logging
□ Docker Compose


PHASE 5 — Observability
-----------------------
□ Prometheus
□ Grafana
□ Metrics
□ OpenTelemetry
□ Distributed tracing


PHASE 6 — Kubernetes
--------------------
□ Docker images
□ Kubernetes Pods
□ Deployments
□ Services
□ ConfigMaps
□ Secrets
□ Ingress
□ Readiness
□ Liveness
□ HPA


PHASE 7 — Production
--------------------
□ CI/CD
□ Integration tests
□ Load testing
□ Failure testing
□ Deployment strategies
□ Security
□ Performance tuning
```

---

# 31. Why This Project Is Valuable

This project is intentionally more than a collection of CRUD APIs.

The main learning is understanding:

```text
Normal system
     ↓
Dependency failure
     ↓
System behavior
     ↓
Failure reproduction
     ↓
Resilience pattern
     ↓
Concurrency testing
     ↓
Production trade-off
```

The same approach can be applied to real backend systems involving:

- payment processing
- order management
- inventory
- user management
- cloud APIs
- distributed services
- AI/GenAI backends
- event-driven systems

---

# 32. Quick Revision — One Page

```text
MICROSERVICES
│
├── Communication
│   └── HTTP / REST
│
├── Resilience
│   ├── Timeout
│   ├── Retry
│   ├── Exponential Backoff
│   └── Circuit Breaker
│
├── Data Safety
│   ├── Idempotency
│   ├── Transactions
│   └── Unique Constraints
│
├── Caching
│   ├── Redis
│   ├── Cache-aside
│   ├── TTL
│   ├── Invalidation
│   ├── Stale Cache
│   └── Cache Stampede
│
├── Concurrency
│   ├── Race Condition
│   ├── asyncio.Lock
│   └── Per-Key Lock
│
├── Messaging
│   ├── RabbitMQ
│   ├── Producer
│   ├── Consumer
│   ├── ACK
│   └── DLQ
│
├── Gateway
│   └── Nginx
│
├── Observability
│   ├── Logs
│   ├── Metrics
│   └── Tracing
│
└── Deployment
    ├── Docker
    └── Kubernetes
```

---

# Author

**Suresh Babu P**

Python Backend | Microservices | Cloud & Kubernetes | GenAI

---

## Status

🚧 **Actively developed as a hands-on backend and distributed-systems learning project.**
