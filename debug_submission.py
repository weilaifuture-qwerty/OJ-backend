#!/usr/bin/env python3
"""Debug submission endpoint"""

import requests
import json

BASE_URL = "http://localhost:8000"
session = requests.Session()

# Get CSRF and login
csrf_response = session.get(f"{BASE_URL}/api/csrf/")
csrf_token = session.cookies.get('csrftoken')

headers = {
    'X-CSRFToken': csrf_token,
    'Content-Type': 'application/json'
}

# Login
login_response = session.post(
    f"{BASE_URL}/api/login/", 
    json={"username": "root", "password": "rootroot"}, 
    headers=headers
)
print(f"Login: {login_response.status_code}")

# Check available problems
print("\nChecking problems...")
problems_response = session.get(f"{BASE_URL}/api/problem/")
if problems_response.status_code == 200:
    problems = problems_response.json()
    print(f"Problems response: {json.dumps(problems, indent=2)}")

# Check specific problem
print("\nChecking problem ID 1...")
problem_response = session.get(f"{BASE_URL}/api/problem?problem_id=1")
if problem_response.status_code == 200:
    problem = problem_response.json()
    print(f"Problem 1: {json.dumps(problem.get('data', {}).get('_id'), indent=2)}")

# Try different submission formats
print("\nTrying submissions...")

# Update CSRF token
headers['X-CSRFToken'] = session.cookies.get('csrftoken', csrf_token)

# Try with string problem_id
submission1 = session.post(
    f"{BASE_URL}/api/submission/",
    json={
        "problem_id": "1",
        "language": "Python3", 
        "code": "print(int(input()) + int(input()))"
    },
    headers=headers
)
print(f"\nString problem_id '1': {submission1.status_code}")
print(f"Response: {submission1.json()}")

# Try with integer problem_id  
submission2 = session.post(
    f"{BASE_URL}/api/submission/",
    json={
        "problem_id": 1,
        "language": "Python3",
        "code": "print(int(input()) + int(input()))"
    },
    headers=headers
)
print(f"\nInteger problem_id 1: {submission2.status_code}")
print(f"Response: {submission2.json()}")

# Try with different code format
submission3 = session.post(
    f"{BASE_URL}/api/submission/",
    json={
        "problem_id": 1,
        "language": "Python3",
        "code": "a, b = map(int, input().split())\nprint(a + b)"
    },
    headers=headers
)
print(f"\nWith proper A+B code: {submission3.status_code}")
print(f"Response: {submission3.json()}")