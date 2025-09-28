#!/usr/bin/env python3
"""
Test script for Route Optimization Microservice
Run this script to test the API endpoints
"""

import requests
import json
import time
import socketio

# Configuration
BASE_URL = "http://localhost:5000"
SOCKETIO_URL = "http://localhost:5001"

def test_health_check():
    """Test health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_route_optimization():
    """Test route optimization endpoint"""
    print("\nTesting route optimization...")
    
    test_data = {
        "addresses": [
            "Marine Drive, Mumbai",
            "Bandra Kurla Complex, Mumbai",
            "Powai, Mumbai",
            "Andheri West, Mumbai"
        ],
        "start_location": "Central Kitchen, Mumbai"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/optimize-route",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200 and 'route_id' in result:
            return result['route_id']
        return None
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_get_route(route_id):
    """Test get route endpoint"""
    print(f"\nTesting get route for ID: {route_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/route/{route_id}")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_start_delivery(route_id):
    """Test start delivery endpoint"""
    print(f"\nTesting start delivery for route: {route_id}")
    
    try:
        response = requests.post(f"{BASE_URL}/route/{route_id}/start")
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200 and 'delivery_id' in result:
            return result['delivery_id']
        return None
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_location_update(delivery_id):
    """Test location update endpoint"""
    print(f"\nTesting location update for delivery: {delivery_id}")
    
    test_location = {
        "delivery_id": delivery_id,
        "location": {
            "latitude": 19.0760,
            "longitude": 72.8777,
            "timestamp": time.time()
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/track/update",
            json=test_location,
            headers={'Content-Type': 'application/json'}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_socketio_connection():
    """Test Socket.IO connection"""
    print("\nTesting Socket.IO connection...")
    
    try:
        sio = socketio.Client()
        
        @sio.event
        def connect():
            print("Connected to Socket.IO server")
            sio.emit('join_delivery', {'delivery_id': 'test_delivery'})
        
        @sio.event
        def joined_delivery(data):
            print(f"Joined delivery: {data}")
        
        @sio.event
        def location_update(data):
            print(f"Location update received: {data}")
        
        @sio.event
        def disconnect():
            print("Disconnected from Socket.IO server")
        
        sio.connect(SOCKETIO_URL)
        time.sleep(2)
        sio.disconnect()
        return True
        
    except Exception as e:
        print(f"Socket.IO connection error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("Route Optimization Microservice Test Suite")
    print("=" * 50)
    
    # Test health check
    if not test_health_check():
        print("Health check failed. Make sure the server is running.")
        return
    
    # Test route optimization
    route_id = test_route_optimization()
    if not route_id:
        print("Route optimization failed.")
        return
    
    # Test get route
    if not test_get_route(route_id):
        print("Get route failed.")
        return
    
    # Test start delivery
    delivery_id = test_start_delivery(route_id)
    if not delivery_id:
        print("Start delivery failed.")
        return
    
    # Test location update
    if not test_location_update(delivery_id):
        print("Location update failed.")
        return
    
    # Test Socket.IO connection
    test_socketio_connection()
    
    print("\n" + "=" * 50)
    print("All tests completed!")
    print("=" * 50)

if __name__ == "__main__":
    main()
