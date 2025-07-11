#!/usr/bin/env python3
"""
Simple server startup script
"""

import uvicorn
from run_local import app

if __name__ == "__main__":
    print("🚀 Starting server on port 8001...")
    try:
        uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        import traceback
        traceback.print_exc() 