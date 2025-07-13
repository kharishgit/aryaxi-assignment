from fastapi import FastAPI, HTTPException
import uvicorn
import random

app = FastAPI()

@app.get("/test")
async def test_endpoint():
    if "8001" in sys.argv[1]:  # Simulate failure on port 8001
        raise HTTPException(status_code=500, detail="Simulated backend failure")
    return {"message": "Backend response"}

@app.post("/test")
async def test_post_endpoint():
    return {"message": "Backend POST response"}

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    uvicorn.run(app, host="0.0.0.0", port=port)