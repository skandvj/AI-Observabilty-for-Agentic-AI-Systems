#!/usr/bin/env python3
"""
Test SharePoint/Jira JSON ingestion functionality
"""

import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Any

# Test data - your sample SharePoint/Jira JSON
sharepoint_test_data = {
    "answers": [
        {
            "AnswerID": "e26060b3-4eb6-4c5e-8ca6-e8d8e4c1fb99",
            "MD5": "",
            "Title": "LCY-8920: Fetch verified answers and top rated answers using new index",
            "Text": "<div style=\"border: 1px solid #eee; padding: 5px; margin-bottom: 5px;\"><html> <head></head> <body>  <p>As an <b>&lt;actor&gt;</b>, I want to <b>&lt;intended action&gt;</b>, so that <b>&lt;Goal/benefit&gt;</b>. Include a one sentence description of the desired change.</p>   <h3><a name=\"Details\"></a>Details</h3>   <p>TBD</p>   <h3><a name=\"Telemetry\"></a>Telemetry</h3>   <p>Include any usage activity we want tracked for this feature.</p>   <h3><a name=\"Mockup\"></a>Mockup</h3>   <p>TBD</p>   <h3><a name=\"AcceptanceCriteria\"></a>Acceptance Criteria</h3>   <p>What outcomes do you expect from this ticket? How will you define this as done?</p>   <ul>    <li>Given that &lt;how things begin&gt;, When &lt;action taken&gt;, Then &lt;Outcome of action&gt;</li>    <li>Given that &lt;how things begin&gt;, When &lt;action taken&gt;, Then &lt;Outcome of action&gt;</li>    <li>Given that &lt;how things begin&gt;, When &lt;action taken&gt;, Then &lt;Outcome of action&gt;</li>   </ul>  </body></html></div>",
            "Confidence": 0.67,
            "ExpertRating": 0.0,
            "TrainingCount": 0,
            "Company": "lucy_jira",
            "Source": "https://whatif.atlassian.net/browse/LCY-8920",
            "Cite": "Lucy Jira",
            "author_name": "Nadeem Qureshi",
            "FileName": "https://whatif.atlassian.net/browse/LCY-8920",
            "combinedData": "LCY-8920: Fetch verified answers and top rated answers using new index<div>As an actor, I want to intended action, so that Goal/benefit. Include a one sentence description of the desired change.</div>",
            "documentDate": "2024-01-04T10:49:41.894-0500",
            "createdDate": "2025-04-15T04:54:16Z",
            "updatedDate": "2025-04-14T14:29:52.780-0400"
        },
        {
            "AnswerID": "132035541_14",
            "MD5": "",
            "Title": "2023 Lucy... ",
            "Text": "<img src=\"/Documents/l2-00424/132035541_132035541_14.jpg\" pdfSize=\"1.1701068878173828\"/>",
            "Confidence": 0.66,
            "ExpertRating": 0.0,
            "TrainingCount": 0,
            "Company": "00424",
            "Source": "[ObjectStoreURL]/l2-00424/LucyRFPResponseforAmex240228Final.key",
            "Cite": "RFP Responses",
            "author_name": "",
            "FileName": "Lucy RFP Response for Amex 240228 Final.key",
            "combinedData": "2023 Lucy These materials may not be used for any purposes including sales or marketing without prior written consent of Equals 3, Inc, dba Lucy for each individual use. Lucy is available as a web App, she can be embedded inside of tools and applications...",
            "documentDate": "2025-04-29T06:59:03Z",
            "createdDate": "2025-04-29T07:06:01Z"
        }
    ]
}

def test_backend_connection():
    """Test if backend is running"""
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running and responding")
            return True
        else:
            print(f"❌ Backend responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return False

def test_sharepoint_ingestion():
    """Test SharePoint/Jira JSON ingestion"""
    try:
        print(f"🧪 Testing SharePoint ingestion with {len(sharepoint_test_data['answers'])} records...")
        
        response = requests.post(
            "http://127.0.0.1:8000/ingest/sharepoint",
            json=sharepoint_test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SharePoint ingestion successful!")
            print(f"   📊 Processed: {result['summary']['total_processed']} records")
            print(f"   📈 Avg Quality Score: {result['summary']['avg_quality_score']}")
            print(f"   ✅ Approved: {result['summary']['approved_records']}")
            print(f"   ⚠️  Flagged: {result['summary']['flagged_records']}")
            print(f"   ⏱️  Processing Time: {result['summary']['processing_time_ms']}ms")
            
            # Show details of processed records
            print("\n📋 Processed Records:")
            for record in result['processed_records']:
                print(f"   • {record['title'][:50]}...")
                print(f"     Quality: {record['quality_score']}, Tags: {', '.join(record['tags'][:3])}")
                
            return True
        else:
            print(f"❌ SharePoint ingestion failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ SharePoint ingestion test failed: {e}")
        return False

def test_export_functionality():
    """Test export functionality"""
    try:
        print("\n🧪 Testing export functionality...")
        
        # Test JSON export
        response = requests.get("http://127.0.0.1:8000/export/records?format=json", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ JSON Export successful! {result['total_records']} records")
        else:
            print(f"❌ JSON Export failed: {response.status_code}")
            return False
        
        # Test CSV export
        response = requests.get("http://127.0.0.1:8000/export/records?format=csv", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ CSV Export successful! {result['total_records']} records")
        else:
            print(f"❌ CSV Export failed: {response.status_code}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Export test failed: {e}")
        return False

def test_analytics_dashboard():
    """Test analytics dashboard"""
    try:
        print("\n🧪 Testing analytics dashboard...")
        
        response = requests.get("http://127.0.0.1:8000/analytics/dashboard", timeout=10)
        if response.status_code == 200:
            result = response.json()
            analytics = result['analytics']
            print("✅ Analytics dashboard working!")
            print(f"   📊 Total Records: {analytics['total_records']}")
            print(f"   🟢 High Quality: {analytics['quality_distribution']['high']}")
            print(f"   🟡 Medium Quality: {analytics['quality_distribution']['medium']}")
            print(f"   🔴 Low Quality: {analytics['quality_distribution']['low']}")
            print(f"   🏢 Companies: {len(analytics['company_distribution'])}")
            print(f"   🔗 Sources: {len(analytics['source_distribution'])}")
            print(f"   🏷️  Tag Cloud Entries: {len(analytics['tag_cloud'])}")
            return True
        else:
            print(f"❌ Analytics failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Analytics test failed: {e}")
        return False

def test_records_endpoint():
    """Test records endpoint"""
    try:
        print("\n🧪 Testing records endpoint...")
        
        response = requests.get("http://127.0.0.1:8000/records", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Records endpoint working! {result['total']} total records")
            if result['records']:
                print(f"   📄 Latest record: {result['records'][-1].get('title', 'Untitled')[:50]}...")
            return True
        else:
            print(f"❌ Records endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Records test failed: {e}")
        return False

def test_local_processing():
    """Test local processing without server"""
    try:
        print("\n🧪 Testing local processing (without server)...")
        
        # Import the functions directly
        import sys
        sys.path.append('.')
        from run_local import transform_sharepoint_answer, extract_tags_from_sharepoint_content, analyze_sharepoint_content_quality
        
        # Test with first answer
        test_answer = sharepoint_test_data['answers'][0]
        
        # Test tag extraction
        tags = extract_tags_from_sharepoint_content(test_answer['combinedData'], test_answer['Title'], test_answer['Company'])
        print(f"✅ Tag extraction: {', '.join(tags)}")
        
        # Test quality analysis
        quality_score, quality_checks = analyze_sharepoint_content_quality(test_answer['combinedData'], tags, "jira")
        print(f"✅ Quality analysis: Score {quality_score}, {len(quality_checks)} checks")
        
        # Test full transformation
        processed_record = transform_sharepoint_answer(test_answer)
        print(f"✅ Full transformation: {processed_record.title[:50]}...")
        print(f"   Quality Score: {processed_record.quality_score}")
        print(f"   Tags: {', '.join(processed_record.tags[:5])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Local processing test failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🚀 Starting Indexing QA System Tests")
    print("=" * 50)
    
    # Test local processing first (doesn't need server)
    test_local_processing()
    
    # Test server connection
    if not test_backend_connection():
        print("\n⚠️  Server tests skipped - backend not running")
        print("💡 To start backend: cd backend && python run_local.py")
        return
    
    # Run server-dependent tests
    tests = [
        test_sharepoint_ingestion,
        test_export_functionality,
        test_analytics_dashboard,
        test_records_endpoint
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        time.sleep(1)  # Brief pause between tests
    
    print("\n" + "=" * 50)
    print(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! System is ready for your SharePoint/Jira JSON data.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    run_all_tests() 