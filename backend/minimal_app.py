#!/usr/bin/env python3
"""
Minimal FastAPI app for testing
"""

from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Server is running"}

@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    print("🚀 Starting minimal server...")
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="info") 