#!/usr/bin/env python3
"""
Quick test script to verify Route Optimization Microservice is working
"""

import requests
import json

def test_microservice():
    """Test the microservice with a simple example"""
    base_url = "http://localhost:5000"
    
    print("🔍 Testing Route Optimization Microservice...")
    print("=" * 50)
    
    # Test 1: Health Check
    print("1. Testing Health Check...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health Check: PASSED")
            print(f"   Response: {response.json()}")
        else:
            print("❌ Health Check: FAILED")
            return False
    except Exception as e:
        print(f"❌ Health Check: ERROR - {e}")
        return False
    
    # Test 2: Route Optimization
    print("\n2. Testing Route Optimization...")
    try:
        test_data = {
            "addresses": [
                "Marine Drive, Mumbai",
                "Bandra Kurla Complex, Mumbai",
                "Powai, Mumbai"
            ],
            "start_location": "Central Kitchen, Mumbai"
        }
        
        response = requests.post(f"{base_url}/optimize-route", json=test_data)
        if response.status_code == 200:
            result = response.json()
            print("✅ Route Optimization: PASSED")
            print(f"   Route ID: {result['route_id']}")
            print(f"   Total Distance: {result['total_distance']} km")
            print(f"   Estimated Time: {result['estimated_time']} minutes")
            route_id = result['route_id']
        else:
            print("❌ Route Optimization: FAILED")
            return False
    except Exception as e:
        print(f"❌ Route Optimization: ERROR - {e}")
        return False
    
    # Test 3: Get Route Details
    print("\n3. Testing Get Route Details...")
    try:
        response = requests.get(f"{base_url}/route/{route_id}")
        if response.status_code == 200:
            print("✅ Get Route Details: PASSED")
            route_data = response.json()
            print(f"   Status: {route_data['status']}")
            print(f"   Addresses: {len(route_data['addresses'])} stops")
        else:
            print("❌ Get Route Details: FAILED")
            return False
    except Exception as e:
        print(f"❌ Get Route Details: ERROR - {e}")
        return False
    
    # Test 4: Start Delivery
    print("\n4. Testing Start Delivery...")
    try:
        response = requests.post(f"{base_url}/route/{route_id}/start")
        if response.status_code == 200:
            result = response.json()
            print("✅ Start Delivery: PASSED")
            print(f"   Delivery ID: {result['delivery_id']}")
            delivery_id = result['delivery_id']
        else:
            print("❌ Start Delivery: FAILED")
            return False
    except Exception as e:
        print(f"❌ Start Delivery: ERROR - {e}")
        return False
    
    # Test 5: Update Location
    print("\n5. Testing Location Update...")
    try:
        location_data = {
            "delivery_id": delivery_id,
            "location": {
                "latitude": 19.0760,
                "longitude": 72.8777,
                "timestamp": 1234567890
            }
        }
        
        response = requests.post(f"{base_url}/track/update", json=location_data)
        if response.status_code == 200:
            print("✅ Location Update: PASSED")
            print("   Location updated successfully")
        else:
            print("❌ Location Update: FAILED")
            return False
    except Exception as e:
        print(f"❌ Location Update: ERROR - {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 ALL TESTS PASSED! Microservice is working perfectly!")
    print("=" * 50)
    return True

if __name__ == "__main__":
    test_microservice()
