High-Throughput Request Gateway with Circuit Breaker
This project implements a Python-based gateway service for AryaXAI Assignment 1, routing requests to backend microservices with a round-robin strategy and circuit breaker pattern.
Design Choices

Framework: FastAPI chosen for its asynchronous support, lightweight design, and similarity to Django REST Framework, ensuring high throughput.
Routing: Round-robin implemented by maintaining an index per service, cycling through available backends. Skips unavailable backends (open circuits).
Circuit Breaker:
State Management: In-memory CircuitBreaker class tracks state (CLOSED, OPEN, HALF_OPEN), failure counts, and cooldown timers.
Logic: Opens after 5 consecutive failures, waits 60 seconds, then transitions to HALF_OPEN for one test request. Success closes the circuit; failure restarts cooldown.
Thread Safety: In-memory state is simple and sufficient for single-process use; production would use Redis for distributed state.


Error Handling: Returns 404 for unknown services, 503 for no available backends, and 502 for backend failures.
Configuration: Loads config.yaml using pyyaml, allowing dynamic service-to-URL mappings.

API Contract

Endpoint: /v1/proxy/{service_name}
Methods: GET, POST, PUT, DELETE
Request: Forwards headers, query params, and body to the selected backend.
Response:
200: Successful response from backend (JSON or text).
404: Service not found in config.yaml.
502: Backend request failed.
503: No available backends (all circuits open).



Setup Instructions

Clone the Repository:
git clone <repository-url>
cd request-gateway


Set Up Virtual Environment:
python3 -m venv venv
source venv/bin/activate


Install Dependencies:
pip install -r requirements.txt


Configure Services:

Edit config.yaml to define service-to-URL mappings (default includes user-service and payment-service).


Run Mock Backends (for testing):
python3 mock_backend.py 8001 & python3 mock_backend.py 8002 & python3 mock_backend.py 8003 &


Run the Gateway:
uvicorn main:app --host 0.0.0.0 --port 8000


Test the Endpoint:
curl http://localhost:8000/v1/proxy/user-service/test
curl -X POST http://localhost:8000/v1/proxy/user-service/test



Sequence Diagram
sequenceDiagram
    participant Client
    participant Gateway
    participant CircuitBreaker
    participant Backend

    Client->>Gateway: Request /v1/proxy/user-service/test
    Gateway->>CircuitBreaker: Select next backend (round-robin)
    CircuitBreaker-->>Gateway: Backend URL (if CLOSED or HALF_OPEN)
    Gateway->>Backend: Forward request
    alt Success
        Backend-->>Gateway: Response
        Gateway->>CircuitBreaker: Record success
        Gateway-->>Client: HTTP 200
    else Failure
        Backend-->>Gateway: Error
        Gateway->>CircuitBreaker: Record failure
        Gateway-->>Client: HTTP 502
    end

Testing

Round-Robin: Verified by sending multiple requests to user-service, alternating between localhost:8001 and localhost:8002.
Circuit Breaker: Tested by stopping a backend, sending 5+ requests to trigger OPEN state, waiting 60 seconds, and confirming HALF_OPEN transition.
Edge Cases: Handled unknown services (404), no available backends (503), and backend failures (502).

Notes for Production

Use Redis or similar for distributed circuit breaker state.
Add logging (e.g., logging module) for monitoring.
Implement rate limiting for high-throughput scenarios.
