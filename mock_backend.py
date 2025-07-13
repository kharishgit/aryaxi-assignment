from fastapi import FastAPI, HTTPException
import uvicorn
import random

app = FastAPI()

@app.get("/test")
async def test_endpoint():
    # Simulate random failures for circuit breaker testing
    if random.random() < 0.2:  # 20% chance of failure
        raise HTTPException(status_code=500, detail="Simulated backend failure")
    return {"message": "Backend response"}

@app.post("/test")
async def test_post_endpoint():
    return {"message": "Backend POST response"}

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    uvicorn.run(app, host="0.0.0.0", port=port)