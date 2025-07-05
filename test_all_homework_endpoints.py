#!/usr/bin/env python3
"""Test script for all homework-related endpoints"""

import requests
import json
from datetime import datetime, timedelta

# Server configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

# Test credentials
ADMIN_USERNAME = "root"
ADMIN_PASSWORD = "rootroot"
STUDENT_USERNAME = "student1"
STUDENT_PASSWORD = "student123"

# Session for maintaining cookies
admin_session = requests.Session()
student_session = requests.Session()


def get_csrf_token(session):
    """Get CSRF token"""
    response = session.get(f"{API_URL}/csrf/")
    if response.status_code == 200:
        return response.cookies.get('csrftoken')
    return None


def login(session, username, password):
    """Login and get session"""
    csrf_token = get_csrf_token(session)
    
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


def test_endpoint(session, method, endpoint, data=None, description=""):
    """Test a single endpoint"""
    csrf_token = get_csrf_token(session)
    headers = {
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json'
    }
    
    url = f"{API_URL}{endpoint}"
    
    try:
        if method == 'GET':
            response = session.get(url)
        elif method == 'POST':
            response = session.post(url, json=data, headers=headers)
        elif method == 'PUT':
            response = session.put(url, json=data, headers=headers)
        elif method == 'DELETE':
            response = session.delete(url, headers=headers)
        else:
            return False, f"Unknown method: {method}"
        
        status_ok = response.status_code in [200, 201]
        result = {
            'endpoint': endpoint,
            'method': method,
            'status': response.status_code,
            'success': status_ok,
            'description': description
        }
        
        if not status_ok:
            try:
                result['error'] = response.json()
            except:
                result['error'] = response.text
        else:
            try:
                result['data'] = response.json()
            except:
                result['data'] = response.text
        
        return status_ok, result
        
    except Exception as e:
        return False, {
            'endpoint': endpoint,
            'method': method,
            'success': False,
            'error': str(e),
            'description': description
        }


def main():
    """Run all endpoint tests"""
    print("=== Testing Homework Backend Endpoints ===\n")
    
    # Login as admin
    print("1. Logging in as admin...")
    if login(admin_session, ADMIN_USERNAME, ADMIN_PASSWORD):
        print("✓ Admin login successful")
    else:
        print("✗ Admin login failed")
        return
    
    # Login as student
    print("\n2. Logging in as student...")
    if login(student_session, STUDENT_USERNAME, STUDENT_PASSWORD):
        print("✓ Student login successful")
    else:
        print("✗ Student login failed")
        return
    
    print("\n=== Testing Admin Endpoints ===\n")
    
    # Test admin endpoints
    admin_tests = [
        # Core homework endpoints
        ('GET', '/admin_homework_list/', None, 'Get admin homework list'),
        ('GET', '/available_students/', None, 'Get available students'),
        ('GET', '/available_groups/', None, 'Get available student groups'),
        ('GET', '/students/group/Group A/', None, 'Get students in Group A'),
        ('GET', '/admin/homework_detail/?id=1', None, 'Get homework detail with student progress'),
        ('GET', '/admin/homework_statistics/', None, 'Get homework statistics'),
        
        # Problem and utility endpoints
        ('GET', '/problem/?limit=10', None, 'Get problems with limit'),
        ('GET', '/problem/?limit=10&keyword=two', None, 'Search problems by keyword'),
        ('GET', '/languages/', None, 'Get available programming languages'),
        ('GET', '/users/?type=student', None, 'Get student users'),
    ]
    
    for method, endpoint, data, desc in admin_tests:
        success, result = test_endpoint(admin_session, method, endpoint, data, desc)
        status_icon = "✓" if success else "✗"
        print(f"{status_icon} {desc}")
        print(f"  {method} {endpoint} - Status: {result['status']}")
        if not success and 'error' in result:
            print(f"  Error: {result['error']}")
        print()
    
    # Test homework creation
    print("Testing homework creation...")
    homework_data = {
        'title': 'Test Homework API',
        'description': 'Testing all endpoints',
        'due_date': (datetime.now() + timedelta(days=7)).isoformat(),
        'problem_ids': [1, 2],  # Assuming problems 1 and 2 exist
        'student_ids': [],  # Assign to all students
        'allow_late_submission': True,
        'late_penalty_percent': 10,
        'max_attempts': 3,
        'auto_grade': True
    }
    
    success, result = test_endpoint(admin_session, 'POST', '/admin_create_homework/', homework_data, 'Create new homework')
    status_icon = "✓" if success else "✗"
    print(f"{status_icon} Create new homework")
    if success:
        homework_id = result['data']['data']['id']
        print(f"  Created homework ID: {homework_id}")
        
        # Test update endpoint
        update_data = {
            'title': 'Updated Test Homework',
            'description': 'Updated description'
        }
        success, result = test_endpoint(admin_session, 'PUT', f'/admin/homework/{homework_id}/', update_data, 'Update homework')
        status_icon = "✓" if success else "✗"
        print(f"\n{status_icon} Update homework")
    print()
    
    print("\n=== Testing Student Endpoints ===\n")
    
    # Test student endpoints
    student_tests = [
        ('GET', '/student_homework/', None, 'Get student homework list'),
        ('GET', '/homework/list/', None, 'Get homework list (RESTful)'),
        ('GET', '/student_homework/?status=assigned', None, 'Get assigned homework'),
        ('GET', '/homework_progress/', None, 'Get homework progress counts'),
        ('GET', '/student_homework_detail/?id=1', None, 'Get homework detail (query param)'),
        ('GET', '/homework/1/', None, 'Get homework detail (RESTful)'),
        ('GET', '/homework/1/submissions/', None, 'Get homework submissions'),
        ('GET', '/submission_exists/?problem_id=1', None, 'Check if submission exists'),
    ]
    
    for method, endpoint, data, desc in student_tests:
        success, result = test_endpoint(student_session, method, endpoint, data, desc)
        status_icon = "✓" if success else "✗"
        print(f"{status_icon} {desc}")
        print(f"  {method} {endpoint} - Status: {result['status']}")
        if not success and 'error' in result:
            print(f"  Error: {result['error']}")
        print()
    
    print("\n=== Summary ===")
    print("All major endpoints have been tested.")
    print("Note: Some endpoints may fail if test data doesn't exist in the database.")
    print("\nTo fully test submission endpoints, you need to:")
    print("1. Submit a solution to a problem first")
    print("2. Then use the submission ID to test homework submission endpoints")


if __name__ == "__main__":
    main()