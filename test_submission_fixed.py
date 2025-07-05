#!/usr/bin/env python3
"""Fixed test script for judge submission with proper session handling"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
session = requests.Session()

# Enable session persistence
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Origin': BASE_URL,
    'Referer': f'{BASE_URL}/'
})

def test_submission():
    print("=== Testing Judge Submission with Fixed Authentication ===\n")
    
    # Step 1: Get CSRF token
    print("1. Getting CSRF token...")
    csrf_response = session.get(f"{BASE_URL}/api/csrf/")
    csrf_token = session.cookies.get('csrftoken')
    print(f"   CSRF Token: {csrf_token[:20]}...")
    
    # Step 2: Login
    print("\n2. Logging in...")
    login_data = {
        "username": "root",
        "password": "rootroot"
    }
    headers = {
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json',
    }
    
    login_response = session.post(f"{BASE_URL}/api/login/", json=login_data, headers=headers)
    if login_response.status_code == 200:
        print("   ✓ Login successful")
        login_result = login_response.json()
        if isinstance(login_result, dict) and 'data' in login_result:
            if isinstance(login_result['data'], dict):
                print(f"   User: {login_result['data'].get('username', 'Unknown')}")
                print(f"   Admin Type: {login_result['data'].get('admin_type', 'Unknown')}")
            else:
                print(f"   Response: {login_result['data']}")
        
        # Update CSRF token after login
        new_csrf = session.cookies.get('csrftoken')
        if new_csrf:
            csrf_token = new_csrf
            print(f"   Updated CSRF Token: {csrf_token[:20]}...")
    else:
        print(f"   ✗ Login failed: {login_response.status_code}")
        print(f"   Response: {login_response.text}")
        return
    
    # Step 3: Verify authentication by checking profile
    print("\n3. Verifying authentication...")
    profile_response = session.get(f"{BASE_URL}/api/profile/")
    if profile_response.status_code == 200:
        profile = profile_response.json()
        if 'data' in profile and profile['data']:
            print(f"   ✓ Authenticated as: {profile['data']['user']['username']}")
        else:
            print("   ✗ Not authenticated")
            return
    else:
        print(f"   ✗ Profile check failed: {profile_response.status_code}")
    
    # Step 4: Check if problem exists
    print("\n4. Checking problem...")
    problem_response = session.get(f"{BASE_URL}/api/problem?problem_id=1")
    if problem_response.status_code == 200:
        problem_data = problem_response.json()
        if problem_data.get('data'):
            problem = problem_data['data']
            print(f"   ✓ Problem found: {problem['title']}")
            print(f"   Time Limit: {problem['time_limit']}ms")
            print(f"   Memory Limit: {problem['memory_limit']}MB")
        else:
            print("   ✗ Problem not found")
            print("   Please create the A+B problem first")
            return
    else:
        print(f"   ✗ Failed to get problem: {problem_response.status_code}")
        return
    
    # Step 5: Submit solution
    print("\n5. Submitting solution...")
    # Need to use the actual database ID, not the display ID
    # The A+B problem has id=5, _id="1"
    submission_data = {
        "problem_id": 5,  # Use the actual database ID
        "language": "Python3",
        "code": "a, b = map(int, input().split())\\nprint(a + b)"
    }
    
    # Update headers with fresh CSRF token
    headers = {
        'X-CSRFToken': session.cookies.get('csrftoken', csrf_token),
        'Content-Type': 'application/json',
    }
    
    submit_response = session.post(
        f"{BASE_URL}/api/submission/", 
        json=submission_data, 
        headers=headers
    )
    
    if submit_response.status_code == 200:
        try:
            response_data = submit_response.json()
            print(f"   ✓ Submission successful")
            print(f"   Response: {response_data}")
            
            # Extract submission ID from various possible formats
            submission_id = None
            if 'data' in response_data:
                if isinstance(response_data['data'], dict):
                    submission_id = response_data['data'].get('submission_id') or response_data['data'].get('id')
                else:
                    submission_id = response_data['data']
            else:
                submission_id = response_data.get('submission_id') or response_data.get('id')
            
            if submission_id:
                print(f"   Submission ID: {submission_id}")
                
                # Step 6: Wait for result
                print("\n6. Waiting for judge result", end="", flush=True)
                for i in range(30):
                    time.sleep(1)
                    print(".", end="", flush=True)
                    
                    result_response = session.get(f"{BASE_URL}/api/submission?id={submission_id}")
                    if result_response.status_code == 200:
                        result_data = result_response.json()
                        if 'data' in result_data and isinstance(result_data['data'], dict):
                            submission = result_data['data']
                            if submission.get('result', -2) != -2:  # Not pending
                                print(f"\n\n   ✓ Judge completed!")
                                
                                # Result codes
                                results = {
                                    0: "Accepted",
                                    -1: "Wrong Answer", 
                                    1: "CPU Time Limit Exceeded",
                                    2: "Time Limit Exceeded",
                                    3: "Memory Limit Exceeded",
                                    4: "Runtime Error",
                                    5: "System Error",
                                    6: "Compile Error",
                                    7: "Partially Accepted"
                                }
                                
                                status_text = results.get(submission['result'], 'Unknown')
                                print(f"   Result: {status_text} ({submission['result']})")
                                
                                if 'statistic_info' in submission:
                                    stats = submission['statistic_info']
                                    if 'time_cost' in stats:
                                        print(f"   Time: {stats['time_cost']}ms")
                                    if 'memory_cost' in stats:
                                        print(f"   Memory: {stats['memory_cost']}KB")
                                
                                if submission['result'] == 0:
                                    print("\n🎉 Success! Judge server is working correctly!")
                                elif submission['result'] == 6:  # Compile error
                                    if 'info' in submission and submission['info']:
                                        print(f"   Compile Error: {submission['info']}")
                                
                                return
                
                print("\n   ✗ Timeout waiting for result")
                print("   The submission might still be in queue")
            else:
                print("   ✗ No submission ID in response")
                
        except json.JSONDecodeError:
            print(f"   ✗ Invalid JSON response: {submit_response.text}")
    else:
        print(f"   ✗ Submission failed: {submit_response.status_code}")
        try:
            error_data = submit_response.json()
            if 'error' in error_data:
                print(f"   Error: {error_data['error']}")
                if 'data' in error_data:
                    print(f"   Details: {error_data['data']}")
        except:
            print(f"   Response: {submit_response.text}")
    
    # Step 7: Debug info
    print("\n7. Debug Information:")
    print(f"   Session cookies: {list(session.cookies.keys())}")
    print(f"   Session ID: {session.cookies.get('sessionid', 'Not found')}")


if __name__ == "__main__":
    test_submission()