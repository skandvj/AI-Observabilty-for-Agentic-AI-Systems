#!/usr/bin/env python3
"""
Script to restore data by ingesting the JSON file
"""

import json
import requests
import time
from pathlib import Path

def ingest_data():
    """Ingest data from the JSON file"""
    
    # Read the JSON file
    json_file = Path("../10_Examples.json")
    if not json_file.exists():
        print(f"❌ JSON file not found: {json_file}")
        return
    
    print(f"📖 Reading data from {json_file}")
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Extract hits
    hits = data.get('hits', [])
    print(f"📊 Found {len(hits)} records to ingest")
    
    # Ingest each record
    success_count = 0
    error_count = 0
    
    for i, hit in enumerate(hits[:10]):  # Limit to first 10 for testing
        try:
            source = hit.get('_source', {})
            
            # Prepare the ingest request
            ingest_data = {
                "record_id": source.get('id', f"record-{i}"),  # Changed from 'id' to 'record_id'
                "title": source.get('title', ''),
                "content": source.get('combined_data', source.get('text', '')),
                "company": source.get('company', ''),
                "source_connector": "SharePoint",  # Default to SharePoint
                "tags": [],
                "metadata": {
                    "file_name": source.get('file_name', ''),
                    "author": source.get('author_name', ''),
                    "created_date": source.get('created_date', ''),
                    "updated_date": source.get('updated_date', ''),
                    "category": source.get('category', ''),
                    "origin": source.get('origin', ''),
                    "container": source.get('container', ''),
                    "document_date": source.get('document_date', ''),
                    "filter1": source.get('filter1', ''),
                    "filter2": source.get('filter2', ''),
                    "filter3": source.get('filter3', ''),
                    "filter4": source.get('filter4', ''),
                    "filter5": source.get('filter5', ''),
                    "enrichstate": source.get('enrichstate', ''),
                    "concepts_nlu": source.get('concepts_nlu', []),
                    "keywords_nlu": source.get('keywords_nlu', []),
                    "entities_nlu": source.get('entities_nlu', []),
                    "meta": source.get('meta', {})
                }
            }
            
            # Send ingest request
            response = requests.post(
                "http://127.0.0.1:8000/ingest",
                json=ingest_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Ingested record {i+1}: {source.get('title', 'Unknown')[:50]}...")
                success_count += 1
            else:
                print(f"❌ Failed to ingest record {i+1}: {response.status_code} - {response.text}")
                error_count += 1
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ Error ingesting record {i+1}: {e}")
            error_count += 1
    
    print(f"\n📊 Ingest Summary:")
    print(f"   ✅ Successfully ingested: {success_count}")
    print(f"   ❌ Failed: {error_count}")
    print(f"   📈 Total processed: {success_count + error_count}")

if __name__ == "__main__":
    print("🚀 Starting data restoration...")
    ingest_data()
    print("✅ Data restoration complete!") 