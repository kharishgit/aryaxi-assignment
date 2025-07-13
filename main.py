from fastapi import FastAPI, HTTPException, Request
from circuit_breaker import CircuitBreaker
import yaml
import httpx
from typing import Dict, List
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="High-Throughput Request Gateway")

# Load configuration from config.yaml
def load_config() -> Dict[str, List[str]]:
    config_path = os.getenv("CONFIG_PATH", "config.yaml")
    logger.info(f"Loading config from: {config_path}")
    try:
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)
        logger.info(f"Loaded config: {config}")
        return config.get("services", {})
    except Exception as e:
        logger.error(f"Config load error: {e}")
        raise

# Initialize circuit breakers for each backend
services = load_config()
circuit_breakers: Dict[str, List[CircuitBreaker]] = {}
current_indices: Dict[str, int] = {}

for service_name, urls in services.items():
    circuit_breakers[service_name] = [CircuitBreaker(url) for url in urls]
    current_indices[service_name] = 0

@app.api_route("/v1/proxy/{service_name}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_request(service_name: str, request: Request):
    logger.info(f"Received request for service: {service_name}, path: {request.url.path}")
    # Check if service exists
    if service_name not in services:
        logger.error(f"Service {service_name} not found")
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

    # Get available circuit breakers
    available_cbs = [cb for cb in circuit_breakers[service_name] if cb.can_send_request()]
    
    if not available_cbs:
        logger.error(f"No available backends for {service_name}")
        raise HTTPException(status_code=503, detail=f"No available backends for {service_name}")

    # Round-robin: select next available backend
    current_index = current_indices[service_name] % len(circuit_breakers[service_name])
    cb = circuit_breakers[service_name][current_index]
    while not cb.can_send_request():
        current_index = (current_index + 1) % len(circuit_breakers[service_name])
        cb = circuit_breakers[service_name][current_index]
        if cb == circuit_breakers[service_name][current_indices[service_name] % len(circuit_breakers[service_name])]:
            logger.error(f"No available backends after full cycle for {service_name}")
            raise HTTPException(status_code=503, detail=f"No available backends for {service_name}")
    
    current_indices[service_name] = (current_index + 1) % len(circuit_breakers[service_name])
    logger.info(f"Routing to backend: {cb.url}")

    # Forward request
    try:
        async with httpx.AsyncClient() as client:
            # Prepare request details
            method = request.method
            # Extract path after service_name
            remaining_path = request.url.path.replace(f"/v1/proxy/{service_name}", "") or "/"
            if remaining_path != "/" and not remaining_path.startswith("/"):
                remaining_path = f"/{remaining_path}"
            url = f"{cb.url}{remaining_path}"
            headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}
            body = await request.body()

            logger.info(f"Forwarding {method} request to {url}")
            # Send request
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                content=body,
                params=request.query_params
            )
            
            # Update circuit breaker on success
            cb.record_success()
            logger.info(f"Successful response from {url}")
            return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
    
    except httpx.RequestError as e:
        # Update circuit breaker on failure
        cb.record_failure()
        logger.error(f"Backend request failed: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Backend request failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)