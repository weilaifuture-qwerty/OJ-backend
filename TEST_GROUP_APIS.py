#!/usr/bin/env python
"""
Test script to verify group-related APIs are working correctly
Run this after starting the Django server to test API responses
"""

import requests
import json

# Base URL - adjust if your server runs on a different port
BASE_URL = "http://localhost:8080/api"

# You'll need to login first to get a session
LOGIN_URL = f"{BASE_URL}/login"

def test_apis():
    # Create a session to maintain cookies
    session = requests.Session()
    
    print("Testing Group-Related APIs...")
    print("=" * 50)
    
    # Test 1: Available Groups
    print("\n1. Testing /api/available_groups")
    try:
        response = session.get(f"{BASE_URL}/available_groups")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            if 'data' in data and 'groups' in data['data']:
                print(f"Found {len(data['data']['groups'])} groups")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 2: Available Students
    print("\n2. Testing /api/available_students")
    try:
        response = session.get(f"{BASE_URL}/available_students")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                print(f"Found {len(data['data'])} students")
                if data['data']:
                    print(f"First student: {json.dumps(data['data'][0], indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 3: Students by Group
    print("\n3. Testing /api/students_by_group")
    try:
        response = session.get(f"{BASE_URL}/students_by_group")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'groups' in data['data']:
                print(f"Found {data['data']['total_groups']} groups with {data['data']['total_students']} total students")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 4: Users endpoint
    print("\n4. Testing /api/users?type=student")
    try:
        response = session.get(f"{BASE_URL}/users", params={"type": "student"})
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                print(f"Found {len(data['data'])} students")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    print("Note: You may need to login first if the APIs require authentication")
    print("Make sure the Django server is running on localhost:8080")
    test_apis()