from enum import Enum
import time

class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, url: str, failure_threshold: int = 5, cooldown_period: int = 60):
        self.url = url
        self.failure_threshold = failure_threshold
        self.cooldown_period = cooldown_period
        self.state = CircuitBreakerState.CLOSED
        self.consecutive_failures = 0
        self.last_failure_time = 0
        self.is_half_open_tested = False

    def can_send_request(self) -> bool:
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            # Check if cooldown period has passed
            if time.time() - self.last_failure_time >= self.cooldown_period:
                self.state = CircuitBreakerState.HALF_OPEN
                self.is_half_open_tested = False
                return True
            return False
        elif self.state == CircuitBreakerState.HALF_OPEN:
            # Allow one test request
            if not self.is_half_open_tested:
                self.is_half_open_tested = True
                return True
            return False

    def record_success(self):
        self.consecutive_failures = 0
        self.state = CircuitBreakerState.CLOSED
        self.is_half_open_tested = False

    def record_failure(self):
        self.consecutive_failures += 1
        self.last_failure_time = time.time()
        if self.consecutive_failures >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN