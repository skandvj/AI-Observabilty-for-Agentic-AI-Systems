#!/usr/bin/env python3
"""
Minimal test to check imports
"""

try:
    from run_local import app
    print("✅ App imported successfully")
    
    # Test database initialization
    import sqlite3
    conn = sqlite3.connect("test.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY)")
    conn.close()
    print("✅ Database test successful")
    
    # Test uvicorn import
    import uvicorn
    print("✅ Uvicorn import successful")
    
    print("✅ All tests passed")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 