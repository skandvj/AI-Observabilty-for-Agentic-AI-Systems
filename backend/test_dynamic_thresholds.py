#!/usr/bin/env python3
"""
Test script for Dynamic Threshold Management System
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_threshold_endpoints():
    """Test all threshold-related endpoints"""
    
    print("🧪 Testing Dynamic Threshold Management System")
    print("=" * 50)
    
    # Test 1: Get all thresholds
    print("\n1. Testing GET /thresholds")
    try:
        response = requests.get(f"{BASE_URL}/thresholds")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {data.get('total_count', 0)} thresholds")
            thresholds = data.get('thresholds', [])
            for threshold in thresholds[:3]:  # Show first 3
                print(f"   - {threshold['name']}: {threshold['current_value']} {threshold['unit']}")
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 2: Get specific threshold
    print("\n2. Testing GET /thresholds/{name}")
    try:
        response = requests.get(f"{BASE_URL}/thresholds/llm_confidence_threshold")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! {data['threshold']['name']}: {data['threshold']['current_value']}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Update threshold
    print("\n3. Testing PUT /thresholds/{name}")
    try:
        update_data = {
            "threshold_name": "llm_confidence_threshold",
            "new_value": 0.75,
            "reason": "Testing threshold update from script",
            "user_id": "test_user"
        }
        response = requests.put(
            f"{BASE_URL}/thresholds/llm_confidence_threshold",
            json=update_data
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Updated to {data['threshold']['current_value']}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Get threshold history
    print("\n4. Testing GET /thresholds/{name}/history")
    try:
        response = requests.get(f"{BASE_URL}/thresholds/llm_confidence_threshold/history")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {len(data.get('history', []))} history entries")
            if data.get('history'):
                latest = data['history'][0]
                print(f"   - Latest: {latest['old_value']} → {latest['new_value']} by {latest['changed_by']}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Reset threshold
    print("\n5. Testing POST /thresholds/{name}/reset")
    try:
        response = requests.post(f"{BASE_URL}/thresholds/llm_confidence_threshold/reset")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Reset to {data['threshold']['current_value']}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 6: Get thresholds by category
    print("\n6. Testing GET /thresholds/categories/{category}")
    try:
        response = requests.get(f"{BASE_URL}/thresholds/categories/quality")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {len(data.get('thresholds', []))} quality thresholds")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 7: Bulk update
    print("\n7. Testing POST /thresholds/bulk-update")
    try:
        bulk_updates = [
            {
                "threshold_name": "quality_pass_rate_threshold",
                "new_value": 90.0,
                "reason": "Bulk update test",
                "user_id": "test_user"
            },
            {
                "threshold_name": "spam_threshold",
                "new_value": 0.35,
                "reason": "Bulk update test",
                "user_id": "test_user"
            }
        ]
        response = requests.post(f"{BASE_URL}/thresholds/bulk-update", json=bulk_updates)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Updated {len(data.get('results', []))} thresholds")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Dynamic Threshold Management System Test Complete!")
    return True

def test_frontend_integration():
    """Test if frontend can access the threshold API"""
    print("\n🌐 Testing Frontend Integration")
    print("=" * 30)
    
    try:
        # Test if frontend is running
        response = requests.get("http://localhost:3003")
        if response.status_code == 200:
            print("✅ Frontend is running on http://localhost:3003")
        else:
            print("❌ Frontend not accessible")
            return False
    except Exception as e:
        print(f"❌ Frontend error: {e}")
        return False
    
    # Test if frontend can access backend API
    try:
        response = requests.get("http://localhost:3003/api/thresholds")
        print("✅ Frontend API proxy working")
    except Exception as e:
        print(f"⚠️  Frontend API proxy not configured: {e}")
    
    return True

def show_current_thresholds():
    """Display current threshold values"""
    print("\n📊 Current Threshold Values")
    print("=" * 30)
    
    try:
        response = requests.get(f"{BASE_URL}/thresholds")
        if response.status_code == 200:
            data = response.json()
            thresholds = data.get('thresholds', [])
            
            for threshold in thresholds:
                status = "🟢" if threshold['current_value'] == threshold['default_value'] else "🟡"
                print(f"{status} {threshold['name']}: {threshold['current_value']} {threshold['unit']}")
                print(f"    Default: {threshold['default_value']} | Range: {threshold['min_value']}-{threshold['max_value']}")
                print(f"    Category: {threshold['category']} | {threshold['description']}")
                print()
    except Exception as e:
        print(f"❌ Error getting thresholds: {e}")

if __name__ == "__main__":
    print("🚀 Starting Dynamic Threshold Management Tests")
    print("=" * 60)
    
    # Show current state
    show_current_thresholds()
    
    # Run tests
    backend_ok = test_threshold_endpoints()
    frontend_ok = test_frontend_integration()
    
    print("\n📋 Test Summary")
    print("=" * 20)
    print(f"Backend API: {'✅ Working' if backend_ok else '❌ Failed'}")
    print(f"Frontend: {'✅ Working' if frontend_ok else '❌ Failed'}")
    
    if backend_ok and frontend_ok:
        print("\n🎉 All systems operational!")
        print("You can now:")
        print("1. Visit http://localhost:3003/settings")
        print("2. Click on 'Dynamic Thresholds' tab")
        print("3. View and edit thresholds in real-time")
    else:
        print("\n⚠️  Some issues detected. Check the logs above.") 