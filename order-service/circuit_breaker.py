import time

class CircuitOpenException(Exception):
    pass

class CircuitBreaker:

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __init__(self, failure_threshold=3, recovery_timeout=10):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self.failure_count = 0
        self.state = self.CLOSED
        self.opened_at = None

    def can_execute(self):

        if self.state == self.CLOSED:
            return True

        if self.state == self.OPEN:

            elapsed = time.time() - self.opened_at

            if elapsed >= self.recovery_timeout:

                self.state = self.HALF_OPEN

                print("Circuit → HALF_OPEN")

                return True

            return False

        if self.state == self.HALF_OPEN:
            return True

        return False

    def record_success(self):

        self.failure_count = 0
        self.state = self.CLOSED

        print("Circuit → CLOSED")

    def record_failure(self):

        self.failure_count += 1

        print(f"Failure count: {self.failure_count}")

        if self.failure_count >= self.failure_threshold:

            self.state = self.OPEN
            self.opened_at = time.time()

            print("Circuit → OPEN")