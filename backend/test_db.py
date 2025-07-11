#!/usr/bin/env python3
"""
Test script to debug database issues
"""

import sqlite3
import json

DB_PATH = "indexing_qa.db"

def test_db_read():
    """Test reading from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM processed_records LIMIT 1")
        row = cursor.fetchone()
        
        if row:
            print(f"Row has {len(row)} columns")
            print(f"Column 4 (tags): {row[4]}")
            print(f"Column 9 (quality_checks): {row[9]}")
            print(f"Column 10 (content_metadata): {row[10]}")
            print(f"Column 14 (llm_suggestions): {row[14]}")
            
            # Test JSON parsing
            try:
                tags = json.loads(row[4]) if row[4] else []
                print(f"Tags parsed successfully: {tags}")
            except Exception as e:
                print(f"Error parsing tags: {e}")
            
            try:
                quality_checks = json.loads(row[9]) if row[9] else []
                print(f"Quality checks parsed successfully: {quality_checks}")
            except Exception as e:
                print(f"Error parsing quality_checks: {e}")
            
            try:
                content_metadata = json.loads(row[10]) if row[10] else {}
                print(f"Content metadata parsed successfully: {content_metadata}")
            except Exception as e:
                print(f"Error parsing content_metadata: {e}")
            
            try:
                llm_suggestions = json.loads(row[14]) if row[14] else []
                print(f"LLM suggestions parsed successfully: {llm_suggestions}")
            except Exception as e:
                print(f"Error parsing llm_suggestions: {e}")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_db_read() 