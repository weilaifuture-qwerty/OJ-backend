#!/usr/bin/env python3
"""Test script to verify judge server submission API"""

import requests
import json
import time
from datetime import datetime

# Server configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

# Test credentials
USERNAME = "root"
PASSWORD = "rootroot"

# Session for maintaining cookies
session = requests.Session()


def get_csrf_token():
    """Get CSRF token"""
    response = session.get(f"{API_URL}/csrf/")
    if response.status_code == 200:
        return response.cookies.get('csrftoken')
    return None


def login(username, password):
    """Login and get session"""
    csrf_token = get_csrf_token()
    
    headers = {
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json'
    }
    
    data = {
        'username': username,
        'password': password
    }
    
    response = session.post(f"{API_URL}/login/", json=data, headers=headers)
    return response.status_code == 200


def get_problem_info(problem_id="1"):
    """Get problem information"""
    response = session.get(f"{API_URL}/problem?problem_id={problem_id}")
    if response.status_code == 200:
        return response.json()['data']
    return None


def get_languages():
    """Get available programming languages"""
    response = session.get(f"{API_URL}/languages/")
    if response.status_code == 200:
        return response.json()['data']
    return []


def submit_code(problem_id, code, language, contest_id=None):
    """Submit code to judge server"""
    csrf_token = get_csrf_token()
    
    headers = {
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json'
    }
    
    data = {
        'problem_id': problem_id,
        'language': language,
        'code': code
    }
    
    if contest_id:
        data['contest_id'] = contest_id
    
    print(f"\nSubmitting code to problem {problem_id}...")
    print(f"Language: {language}")
    print(f"Code length: {len(code)} characters")
    
    response = session.post(f"{API_URL}/submission/", json=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        if 'data' in result and isinstance(result['data'], dict):
            return result['data']
        else:
            print(f"Unexpected response format: {result}")
            return None
    else:
        print(f"Submission failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return None


def get_submission_result(submission_id):
    """Get submission result"""
    response = session.get(f"{API_URL}/submission?id={submission_id}")
    if response.status_code == 200:
        return response.json()['data']
    return None


def wait_for_result(submission_id, timeout=30):
    """Wait for submission to be judged"""
    print(f"\nWaiting for submission {submission_id} to be judged...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        result = get_submission_result(submission_id)
        if result:
            # Check if judging is complete
            if result['result'] != -2:  # -2 means pending/judging
                return result
        
        time.sleep(1)
        print(".", end="", flush=True)
    
    print("\nTimeout waiting for result")
    return None


def test_simple_submission():
    """Test a simple A+B problem submission"""
    # Simple Python code for A+B problem
    code = """a, b = map(int, input().split())
print(a + b)"""
    
    # Submit the code
    submission = submit_code(
        problem_id=5,  # A+B problem has database ID 5
        code=code,
        language="Python3"
    )
    
    if submission:
        print(f"\nSubmission created with ID: {submission['submission_id']}")
        
        # Wait for result
        result = wait_for_result(submission['submission_id'])
        
        if result:
            print(f"\n\nSubmission Result:")
            print(f"Status: {result['result']}")
            if isinstance(result.get('statistic_info'), dict):
                print(f"Time: {result['statistic_info'].get('time_cost', 'N/A')} ms")
                print(f"Memory: {result['statistic_info'].get('memory_cost', 'N/A')} KB")
            elif isinstance(result.get('statistic_info'), str):
                print(f"Info: {result['statistic_info']}")
            
            # Map result codes to status
            status_map = {
                -2: "Pending",
                -1: "Wrong Answer",
                0: "Accepted",
                1: "CPU Time Limit Exceeded",
                2: "Time Limit Exceeded",
                3: "Memory Limit Exceeded",
                4: "Runtime Error",
                5: "System Error",
                6: "Compile Error",
                7: "Partially Accepted"
            }
            
            status_text = status_map.get(result['result'], "Unknown")
            print(f"Status Text: {status_text}")
            
            if result['result'] == 6:  # Compile Error
                print(f"\nCompile Error Info:")
                print(result.get('statistic_info', {}).get('err_info', 'No error info'))
            
            return result['result'] == 0  # Return True if Accepted
    
    return False


def test_judge_server_connection():
    """Test if judge server is connected"""
    response = session.get(f"{API_URL}/admin/judge_server/")
    if response.status_code == 200:
        data = response.json().get('data', [])
        # Handle both list and dict responses
        if isinstance(data, dict):
            servers = data.get('results', [])
        else:
            servers = data if isinstance(data, list) else []
            
        if servers:
            print("\nJudge Servers:")
            for server in servers:
                if isinstance(server, dict):
                    print(f"- {server.get('hostname', 'Unknown')} ({server.get('ip', 'Unknown')})")
                    print(f"  Status: {'Normal' if server.get('status') == 'normal' else 'Abnormal'}")
                    print(f"  Task Number: {server.get('task_number', 0)}")
                    print(f"  CPU: {server.get('cpu_usage', 0)}%")
                    print(f"  Memory: {server.get('memory_usage', 0)}%")
                else:
                    print(f"- Server: {server}")
            return True
        else:
            print("\nNo judge servers found!")
            return False
    else:
        print(f"\nFailed to get judge server info (Status: {response.status_code})")
        print(f"Note: This is normal if you're not logged in as admin")
        return True  # Continue anyway


def main():
    """Run all tests"""
    print("=== Testing Judge Server API ===\n")
    
    # Step 1: Login
    print("1. Logging in...")
    if login(USERNAME, PASSWORD):
        print("✓ Login successful")
    else:
        print("✗ Login failed")
        return
    
    # Step 2: Check judge server connection
    print("\n2. Checking judge server connection...")
    if not test_judge_server_connection():
        print("✗ Judge server not connected or not accessible")
        print("\nPlease ensure:")
        print("1. Judge server is running")
        print("2. Judge server is properly configured in the admin panel")
        print("3. You have admin permissions to view judge server status")
        # Continue anyway to test submission
    
    # Step 3: Get available languages
    print("\n3. Getting available languages...")
    languages = get_languages()
    if languages:
        print("✓ Available languages:")
        for lang in languages:
            if isinstance(lang, dict):
                print(f"  - {lang.get('name', lang.get('text', 'Unknown'))} ({lang.get('description', lang.get('value', ''))})")
            else:
                print(f"  - {lang}")
    else:
        print("✗ Failed to get languages")
        return
    
    # Step 4: Get problem info
    print("\n4. Getting problem information...")
    problem = get_problem_info("1")
    if problem:
        print(f"✓ Problem found: {problem['title']}")
        print(f"  Difficulty: {problem['difficulty']}")
        print(f"  Time Limit: {problem['time_limit']} ms")
        print(f"  Memory Limit: {problem['memory_limit']} MB")
    else:
        print("✗ Problem not found")
        print("  Make sure problem ID 1 exists in the system")
        return
    
    # Step 5: Test submission
    print("\n5. Testing code submission...")
    success = test_simple_submission()
    
    if success:
        print("\n\n✓ Judge server API is working correctly!")
        print("  Code was submitted and judged successfully.")
    else:
        print("\n\n✗ Submission test failed")
        print("\nPossible issues:")
        print("1. Judge server is not running")
        print("2. Judge server is not properly configured")
        print("3. Problem test data is not set up")
        print("4. Network connectivity issues")
    
    # Additional diagnostics
    print("\n\n=== Diagnostics ===")
    print(f"API Base URL: {API_URL}")
    print(f"Current time: {datetime.now()}")
    
    # Try to get recent submissions
    print("\nRecent submissions:")
    response = session.get(f"{API_URL}/submissions/", params={"limit": 5})
    if response.status_code == 200:
        submissions = response.json().get('data', {}).get('results', [])
        for sub in submissions:
            print(f"- ID: {sub['id']}, Problem: {sub['problem']}, "
                  f"Result: {sub['result']}, Time: {sub['create_time']}")
    else:
        print("Failed to get recent submissions")


if __name__ == "__main__":
    main()