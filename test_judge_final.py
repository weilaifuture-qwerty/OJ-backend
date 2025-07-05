#!/usr/bin/env python3
"""Final judge server test with automatic problem ID detection"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
session = requests.Session()

def main():
    print("=== OnlineJudge Judge Server Test ===\n")
    
    # Step 1: Get CSRF token
    print("1. Getting CSRF token...")
    csrf_response = session.get(f"{BASE_URL}/api/csrf/")
    csrf_token = session.cookies.get('csrftoken')
    if not csrf_token:
        print("   ✗ Failed to get CSRF token")
        return
    print(f"   ✓ Got CSRF token")
    
    # Step 2: Login
    print("\n2. Logging in as root...")
    headers = {
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json',
    }
    
    login_response = session.post(
        f"{BASE_URL}/api/login/", 
        json={"username": "root", "password": "rootroot"}, 
        headers=headers
    )
    
    if login_response.status_code != 200:
        print(f"   ✗ Login failed: {login_response.status_code}")
        return
    print("   ✓ Login successful")
    
    # Step 3: Find A+B problem
    print("\n3. Finding A+B problem...")
    problem_id = None
    
    # First try by display ID
    problem_response = session.get(f"{BASE_URL}/api/problem?problem_id=1")
    if problem_response.status_code == 200:
        problem_data = problem_response.json().get('data')
        if problem_data and 'A+B' in problem_data.get('title', ''):
            # Get the actual database ID
            # The API returns the problem, we need to extract its real ID
            # This is tricky as the API might not return the database ID
            print(f"   Found: {problem_data['title']} (display ID: {problem_data['_id']})")
            
            # Try to get all problems to find the real ID
            # Using a large limit to get all problems
            all_problems = session.get(f"{BASE_URL}/api/problem/?limit=100")
            if all_problems.status_code == 200:
                problems_list = all_problems.json().get('data', {}).get('results', [])
                for p in problems_list:
                    if p.get('_id') == '1' and 'A+B' in p.get('title', ''):
                        problem_id = p.get('id')
                        break
    
    # If not found, hardcode based on our check
    if not problem_id:
        print("   Using known problem ID: 5")
        problem_id = 5
    else:
        print(f"   ✓ Found problem with ID: {problem_id}")
    
    # Step 4: Submit solution
    print("\n4. Submitting solution...")
    submission_data = {
        "problem_id": problem_id,
        "language": "Python3",
        "code": "a, b = map(int, input().split())\\nprint(a + b)"
    }
    
    # Update CSRF token
    headers['X-CSRFToken'] = session.cookies.get('csrftoken', csrf_token)
    
    submit_response = session.post(
        f"{BASE_URL}/api/submission/", 
        json=submission_data, 
        headers=headers
    )
    
    if submit_response.status_code != 200:
        print(f"   ✗ Submission failed: {submit_response.status_code}")
        print(f"   Response: {submit_response.json()}")
        return
    
    response_data = submit_response.json()
    if 'error' in response_data and response_data['error'] not in ['success', None]:
        print(f"   ✗ Submission error: {response_data}")
        return
    
    # Extract submission ID
    submission_id = None
    if 'data' in response_data:
        if isinstance(response_data['data'], dict):
            submission_id = response_data['data'].get('submission_id')
        else:
            submission_id = response_data['data']
    
    if not submission_id:
        print("   ✗ No submission ID returned")
        return
    
    print(f"   ✓ Submission created: ID {submission_id}")
    
    # Step 5: Wait for result
    print("\n5. Waiting for judge result", end="", flush=True)
    start_time = time.time()
    
    while time.time() - start_time < 30:
        time.sleep(1)
        print(".", end="", flush=True)
        
        result_response = session.get(f"{BASE_URL}/api/submission?id={submission_id}")
        if result_response.status_code == 200:
            result_data = result_response.json().get('data', {})
            if isinstance(result_data, dict) and result_data.get('result', -2) != -2:
                print("\n")
                
                # Result mapping
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
                
                result_code = result_data['result']
                status_text = results.get(result_code, 'Unknown')
                
                print(f"   Result: {status_text} (code: {result_code})")
                
                if 'statistic_info' in result_data and isinstance(result_data['statistic_info'], dict):
                    stats = result_data['statistic_info']
                    print(f"   Time: {stats.get('time_cost', 'N/A')}ms")
                    print(f"   Memory: {stats.get('memory_cost', 'N/A')}KB")
                
                if result_code == 0:
                    print("\n✅ SUCCESS! Judge server is working correctly!")
                    print("   The A+B problem was solved and accepted.")
                elif result_code == 6:  # Compile error
                    print(f"\n   ⚠️  Compile Error Details:")
                    if 'info' in result_data:
                        print(f"   {result_data['info']}")
                    if 'statistic_info' in result_data:
                        if isinstance(result_data['statistic_info'], str):
                            print(f"   Error: {result_data['statistic_info']}")
                
                return
    
    print("\n   ✗ Timeout waiting for result")
    print("   The submission might still be in queue")
    
    # Final status check
    print("\n6. Final checks:")
    print(f"   - Django server: ✓ Running")
    print(f"   - Authentication: ✓ Working") 
    print(f"   - Problem exists: ✓ Yes")
    print(f"   - Submission API: ✓ Working")
    print(f"   - Judge result: ⚠️  Timeout")
    print("\n   The judge server might not be running or configured properly.")
    print("   Check: docker ps | grep judge")


if __name__ == "__main__":
    main()