#!/usr/bin/env python3
"""Check if A+B problem exists"""

import requests
import json

# Server configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

# Session for maintaining cookies
session = requests.Session()

def check_problem():
    """Check if problem ID 1 exists"""
    print("Checking for A+B problem...")
    
    try:
        response = session.get(f"{API_URL}/problem?problem_id=1")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data'):
                problem = data['data']
                print(f"\n✓ Problem found!")
                print(f"  Title: {problem.get('title', 'Unknown')}")
                print(f"  ID: {problem.get('_id', 'Unknown')}")
                print(f"  Difficulty: {problem.get('difficulty', 'Unknown')}")
                print(f"  Time Limit: {problem.get('time_limit', 'Unknown')} ms")
                print(f"  Memory Limit: {problem.get('memory_limit', 'Unknown')} MB")
                
                # Check for test cases
                test_case_id = problem.get('test_case_id')
                if test_case_id:
                    print(f"  Test Case ID: {test_case_id}")
                    
                    # Check if test case files exist
                    import os
                    test_case_dir = f"data/test_case/{test_case_id}"
                    if os.path.exists(test_case_dir):
                        files = os.listdir(test_case_dir)
                        test_files = [f for f in files if f.endswith('.in') or f.endswith('.out')]
                        print(f"  Test Files: {len(test_files)} files found")
                    else:
                        print(f"  ⚠️  Test case directory not found: {test_case_dir}")
                
                return True
            else:
                print("\n✗ Problem ID 1 not found!")
                print("\nTo create it, run:")
                print("python create_ab_problem.py")
                return False
        else:
            print(f"\n✗ Failed to check problem (Status: {response.status_code})")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n✗ Cannot connect to server. Is it running?")
        print("Run: python manage.py runserver")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


def create_test_cases_manually():
    """Create test case files manually"""
    import os
    
    print("\nCreating test case files manually...")
    
    test_case_dir = "data/test_case/ab_problem_test"
    os.makedirs(test_case_dir, exist_ok=True)
    
    test_cases = [
        ("1 2", "3"),
        ("10 20", "30"),
        ("100 200", "300"),
        ("-5 5", "0"),
        ("999 1", "1000"),
    ]
    
    for i, (input_data, output_data) in enumerate(test_cases, 1):
        # Write input file
        with open(f"{test_case_dir}/{i}.in", 'w') as f:
            f.write(input_data + '\n')
        
        # Write output file
        with open(f"{test_case_dir}/{i}.out", 'w') as f:
            f.write(output_data + '\n')
    
    print(f"✓ Created {len(test_cases)} test cases in {test_case_dir}")


if __name__ == "__main__":
    if check_problem():
        print("\n✓ A+B problem is ready for testing!")
    else:
        print("\n Creating test cases manually...")
        create_test_cases_manually()
        print("\n You still need to create the problem in the database.")
        print(" Use Django admin or run the create script.")