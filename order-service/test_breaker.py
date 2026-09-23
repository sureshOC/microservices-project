from circuit_breaker import CircuitBreaker
import time

breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=10
)

print(breaker.state)

breaker.record_failure()
breaker.record_failure()
breaker.record_failure()

print(breaker.state)

time.sleep(10)

print(breaker.can_execute())

breaker.record_success()

print(breaker.state)