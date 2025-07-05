#!/usr/bin/env python3
"""Quick test for judge submission"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
session = requests.Session()

# Get CSRF token
print("Getting CSRF token...")
csrf_response = session.get(f"{BASE_URL}/api/csrf/")
csrf_token = session.cookies.get('csrftoken')
print(f"CSRF Token: {csrf_token[:20]}...")

# Login
print("\nLogging in...")
login_data = {
    "username": "root",
    "password": "rootroot"
}
headers = {
    'X-CSRFToken': csrf_token,
    'Content-Type': 'application/json'
}
login_response = session.post(f"{BASE_URL}/api/login/", json=login_data, headers=headers)
print(f"Login status: {login_response.status_code}")

# Check problem
print("\nChecking problem 1...")
problem_response = session.get(f"{BASE_URL}/api/problem?problem_id=1")
if problem_response.status_code == 200:
    print("✓ Problem found")
else:
    print("✗ Problem not found")
    print("Please create the A+B problem first")
    exit(1)

# Submit solution
print("\nSubmitting solution...")
submission_data = {
    "problem_id": "1",
    "language": "Python3",
    "code": "a, b = map(int, input().split())\nprint(a + b)"
}
headers['X-CSRFToken'] = session.cookies.get('csrftoken')
submit_response = session.post(f"{BASE_URL}/api/submission/", json=submission_data, headers=headers)

if submit_response.status_code == 200:
    response_data = submit_response.json()
    print(f"Response: {response_data}")
    
    # Handle different response formats
    if 'data' in response_data:
        if isinstance(response_data['data'], dict):
            submission_id = response_data['data'].get('submission_id') or response_data['data'].get('id')
        else:
            submission_id = response_data['data']
    else:
        submission_id = response_data.get('submission_id') or response_data.get('id')
    
    if submission_id:
        print(f"✓ Submission created: {submission_id}")
    
    # Wait for result
    print("\nWaiting for judge result", end="")
    for i in range(30):
        time.sleep(1)
        print(".", end="", flush=True)
        
        result_response = session.get(f"{BASE_URL}/api/submission?id={submission_id}")
        if result_response.status_code == 200:
            result_data = result_response.json()['data']
            if result_data['result'] != -2:  # Not pending
                print(f"\n\n✓ Judge completed!")
                print(f"Result: {result_data['result']}")
                
                # Result codes
                results = {
                    0: "Accepted",
                    -1: "Wrong Answer", 
                    1: "CPU Time Limit Exceeded",
                    2: "Time Limit Exceeded",
                    3: "Memory Limit Exceeded",
                    4: "Runtime Error",
                    5: "System Error",
                    6: "Compile Error"
                }
                
                print(f"Status: {results.get(result_data['result'], 'Unknown')}")
                if result_data['result'] == 0:
                    print("\n🎉 Success! Judge server is working correctly!")
                break
    else:
        print("\n✗ Timeout waiting for result")
else:
    print(f"✗ Submission failed: {submit_response.status_code}")
    print(submit_response.json())