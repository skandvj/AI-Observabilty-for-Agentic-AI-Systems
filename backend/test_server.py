#!/usr/bin/env python3
"""
Simple test script to check server startup
"""

import uvicorn
from run_local import app

if __name__ == "__main__":
    print("Starting server...")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info") 