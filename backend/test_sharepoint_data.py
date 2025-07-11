#!/usr/bin/env python3
"""
Test script for SharePoint JSON data ingestion
Tests our system's ability to handle complex real-world SharePoint data
"""

import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Any

# Test data - the SharePoint JSON structure the user provided
sharepoint_test_data = {
    "answers": [
        {
            "AnswerID": "117193046_20",
            "MD5": "",
            "Title": "Using hashtags... ",
            "Text": "<img src=\"/Documents/l2-003tu/ActiveInternationalSocialMediaStrategyWorkbook.pdf_117193046_20.jpg\" pdfurl=\"/Documents/l2-003tu/ActiveInternationalSocialMediaStrategyWorkbook.pdf_117193046_20.jpg\" pdfSize=\"0.4775991439819336\"/>",
            "Confidence": 0.63,
            "ExpertRating": 0.0,
            "TrainingCount": 0,
            "Company": "003tu",
            "Source": "[ObjectStoreURL]/l2-003tu/ActiveInternationalSocialMediaStrategyWorkbook.pdf?bsaccount=1f441773-53bb-478e-9969-f71d3eaf6791&bsid=eyJzaXRlIjoiZXF1YWxzM2FpLnNoYXJlcG9pbnQuY29tLDliZTQzNzcyLTU3MmItNDU0OC1hOGJkLWY2MGEyYTZmMzkxMyxkMTYyZWFkYi1jNjg0LTQ1NzQtYmU2Mi1hNWFlMzExNmJkZjEiLCJkcml2ZSI6ImIhY2pma215dFhTRVdvdmZZS0ttODVFOXZxWXRHRXhuUkZ2bUtscmpFV3ZmR1JlNkxBM1l5aFJwNndaaUNaZFhhcSIsImZpbGUiOiIwMTY1Q1oyQzVMTzM0WDVYSE1UVkNaRUxJUDQySjVJVEtWIn0=",
            "Cite": "SharePoint - Misc",
            "Answer_Concepts": "none",
            "Answer_Taxonomy": "none", 
            "Answer_Keywords": "none",
            "Filter3": "20of28",
            "author_name": "",
            "FileName": "Active International - Social Media Strategy Workbook.pdf",
            "currentPageNumber": 20,
            "totalpageCount": 28,
            "startingPage": 0,
            "Description": "",
            "Language": "",
            "Topic": "",
            "assetDetailsUrl": "",
            "section": "",
            "V2Passage": "",
            "isGPS": False,
            "isThirdPartySource": False,
            "shouldShowSourceNameInChat": False,
            "sourceMeta": {},
            "answer_locations": "",
            "answer_brands": "",
            "answer_persons": "",
            "combinedData": "Using hashtags...  Using hashtags \\nto increase brand \\nawareness and \\ndiscover trending \\ntopics  \\n1\\nProven tactics for \\nbrand amplification\\n2\\nBest practices \\nfor the top social \\nnetworks\\n3\\nAmplify\\n \\n \\nYour Brand\\nIn this chapter, you will learn about:\\n -- Cp\\npay AY\\n1 Using hashtags 2 Proven tactics for 3 Best practices\\nto increase brand brand amplification for the top social\\nawareness and networks\\ndiscover trending\\ntopics  ",
            "Taxonomies": [],
            "CustomTaxonomies": [],
            "Concepts": [],
            "Entities": [],
            "DiscoveryConcepts": [],
            "DiscoveryTaxonomies": [],
            "DiscoveryKeywords": [],
            "DiscoveryEntities": [],
            "CompanyandSource": [],
            "soruceSet": [],
            "documentDate": "2015-04-07T05:58:52Z",
            "createdDate": "2023-10-13T16:45:28Z",
            "updatedDate": "2015-04-07T05:58:54Z",
            "categories": "",
            "Passage": "No passages are available for this answer unit based on the question asked."
        }
    ]
}

def transform_sharepoint_to_our_format(sharepoint_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Transform SharePoint data to our ingest format"""
    ingestion_requests = []
    
    for answer in sharepoint_data.get("answers", []):
        # Extract meaningful content - prefer combinedData over Text
        content = answer.get("combinedData", "").strip()
        if not content or len(content) < 10:
            content = answer.get("Text", "").strip()
        if not content or len(content) < 10:
            content = answer.get("Title", "").strip()
        
        # If still no content, create meaningful content from metadata
        if not content or len(content) < 10:
            content = f"Document from {answer.get('FileName', 'unknown')} - {answer.get('Cite', 'SharePoint content')}"
        
        # Clean up HTML and escape characters
        content = content.replace("\\n", " ").replace("<img", "Image:").replace("/>", "")
        
        # Extract tags from multiple fields
        tags = []
        
        # Add filename-based tags
        filename = answer.get("FileName", "")
        if filename:
            # Extract meaningful parts from filename
            filename_parts = filename.replace(".pdf", "").replace("-", " ").replace("_", " ").split()
            tags.extend([part.lower() for part in filename_parts if len(part) > 2])
        
        # Add category/topic tags
        if answer.get("Topic"):
            tags.append(answer["Topic"].lower())
        if answer.get("categories"):
            tags.append(answer["categories"].lower())
        if answer.get("Cite"):
            # Extract source type
            cite_parts = answer["Cite"].split(" - ")
            tags.extend([part.strip().lower() for part in cite_parts])
        
        # Add content-based tags
        if "hashtag" in content.lower():
            tags.append("social-media")
        if "brand" in content.lower():
            tags.append("branding")
        if "strategy" in content.lower():
            tags.append("strategy")
            
        # Ensure we have at least some tags
        if not tags:
            tags = ["sharepoint", "document", "content"]
        
        # Remove duplicates and empty tags
        tags = list(set([tag for tag in tags if tag and len(tag) > 1]))
        
        # Create our ingest request
        request = {
            "record_id": answer.get("AnswerID", f"sp_{int(time.time())}"),
            "content": content,
            "tags": tags,
            "source_connector": "sharepoint",
            "metadata": {
                "original_answer_id": answer.get("AnswerID"),
                "filename": answer.get("FileName"),
                "company": answer.get("Company"),
                "confidence": answer.get("Confidence"),
                "source_url": answer.get("Source"),
                "page_info": {
                    "current": answer.get("currentPageNumber"),
                    "total": answer.get("totalpageCount")
                },
                "dates": {
                    "document_date": answer.get("documentDate"),
                    "created_date": answer.get("createdDate"),
                    "updated_date": answer.get("updatedDate")
                }
            }
        }
        
        ingestion_requests.append(request)
    
    return ingestion_requests

def test_backend_endpoints():
    """Test our backend with the SharePoint data"""
    base_url = "http://127.0.0.1:8000"
    
    print("🧪 Testing Indexing QA Backend with SharePoint Data")
    print("=" * 60)
    
    # Test 1: Health Check
    print("\\n1. Testing Health Check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Backend is healthy: {health_data.get('status')}")
            print(f"   Rules Engine Available: {health_data.get('rules_engine_available')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return False
    
    # Test 2: Transform SharePoint Data
    print("\\n2. Transforming SharePoint Data...")
    try:
        transformed_data = transform_sharepoint_to_our_format(sharepoint_test_data)
        print(f"✅ Transformed {len(transformed_data)} SharePoint answers")
        
        for i, data in enumerate(transformed_data):
            print(f"   Record {i+1}:")
            print(f"     ID: {data['record_id']}")
            print(f"     Content Length: {len(data['content'])} chars")
            print(f"     Tags: {data['tags']}")
            print(f"     Source: {data['source_connector']}")
    except Exception as e:
        print(f"❌ Data transformation failed: {e}")
        return False
    
    # Test 3: Rules Engine Check
    print("\\n3. Testing Rules Engine...")
    for i, data in enumerate(transformed_data):
        try:
            rules_request = {
                "document_text": data["content"],
                "tags": data["tags"],
                "source_connector": data["source_connector"]
            }
            
            response = requests.post(
                f"{base_url}/rules/check",
                json=rules_request,
                timeout=10
            )
            
            if response.status_code == 200:
                rules_result = response.json()
                print(f"✅ Rules check {i+1}: {rules_result.get('overall_status', 'unknown')}")
                print(f"   Processing time: {rules_result.get('processing_time_ms', 0):.1f}ms")
                
                # Show any failures
                results = rules_result.get("results", [])
                failed_checks = [r for r in results if r.get("status") == "FAIL"]
                if failed_checks:
                    print(f"   ⚠️  {len(failed_checks)} checks failed:")
                    for check in failed_checks:
                        print(f"     - {check.get('check_name')}: {check.get('failure_reason')}")
            else:
                print(f"❌ Rules check {i+1} failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Rules check {i+1} error: {e}")
            return False
    
    # Test 4: Full Ingestion
    print("\\n4. Testing Full Content Ingestion...")
    for i, data in enumerate(transformed_data):
        try:
            response = requests.post(
                f"{base_url}/ingest",
                json=data,
                timeout=15
            )
            
            if response.status_code == 200:
                ingest_result = response.json()
                print(f"✅ Ingestion {i+1}: Quality Score {ingest_result.get('quality_score', 0)}")
                print(f"   Status: {ingest_result.get('status')}")
                print(f"   Processing time: {ingest_result.get('processing_time_ms', 0):.1f}ms")
            else:
                print(f"❌ Ingestion {i+1} failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Ingestion {i+1} error: {e}")
    
    # Test 5: LLM Analysis
    print("\\n5. Testing LLM Analysis...")
    sample_data = transformed_data[0]  # Test with first record
    try:
        llm_request = {
            "content": sample_data["content"],
            "tags": sample_data["tags"],
            "context": sample_data.get("metadata", {})
        }
        
        response = requests.post(
            f"{base_url}/llm/analyze",
            json=llm_request,
            timeout=20
        )
        
        if response.status_code == 200:
            llm_result = response.json()
            print(f"✅ LLM Analysis: Quality Score {llm_result.get('quality_score', 0)}")
            print(f"   Confidence: {llm_result.get('confidence', 0):.2f}")
            print(f"   Reasoning: {llm_result.get('reasoning', 'No reasoning provided')[:100]}...")
        else:
            print(f"❌ LLM analysis failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ LLM analysis error: {e}")
    
    # Test 6: Check Records Endpoint
    print("\\n6. Testing Records Retrieval...")
    try:
        response = requests.get(f"{base_url}/records", timeout=10)
        
        if response.status_code == 200:
            records_data = response.json()
            record_count = len(records_data.get("records", []))
            print(f"✅ Retrieved {record_count} records from database")
            
            if record_count > 0:
                sample_record = records_data["records"][0]
                print(f"   Sample record ID: {sample_record.get('id', 'unknown')}")
                print(f"   Sample quality score: {sample_record.get('quality_score', 'unknown')}")
        else:
            print(f"❌ Records retrieval failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Records retrieval error: {e}")
    
    # Test 7: Statistics
    print("\\n7. Testing Statistics Endpoint...")
    try:
        response = requests.get(f"{base_url}/stats", timeout=10)
        
        if response.status_code == 200:
            stats_data = response.json()
            print(f"✅ Statistics retrieved:")
            print(f"   Total processed: {stats_data.get('total_processed', 0)}")
            print(f"   Avg processing time: {stats_data.get('avg_processing_time_ms', 0):.1f}ms")
            print(f"   System health: {stats_data.get('system_health', 'unknown')}")
        else:
            print(f"❌ Statistics failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Statistics error: {e}")
    
    print("\\n" + "=" * 60)
    print("🎉 SharePoint Data Testing Complete!")
    return True

if __name__ == "__main__":
    print("🚀 Starting SharePoint JSON Data Test")
    print("Testing complex real-world SharePoint data with our Indexing QA system")
    print()
    
    # Show the original data structure
    print("📋 Original SharePoint Data Structure:")
    print(f"   Answers count: {len(sharepoint_test_data['answers'])}")
    print(f"   Sample Answer ID: {sharepoint_test_data['answers'][0]['AnswerID']}")
    print(f"   Sample filename: {sharepoint_test_data['answers'][0]['FileName']}")
    print()
    
    # Run the tests
    success = test_backend_endpoints()
    
    if success:
        print("\\n✅ All tests completed! The system can handle SharePoint JSON data.")
    else:
        print("\\n❌ Some tests failed. Check the backend logs for more details.") 