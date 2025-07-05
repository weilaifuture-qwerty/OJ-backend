#!/usr/bin/env python
"""
Test script to verify homework endpoints are working
Run this in your Django shell: python manage.py shell < test_homework_endpoints.py
"""

from django.urls import reverse, resolve
from django.urls.exceptions import NoReverseMatch

# Test endpoints that should exist
test_endpoints = [
    # Student endpoints
    ('GET', '/api/student_homework/'),
    ('GET', '/api/student_homework_detail/'),
    ('GET', '/api/homework_progress/'),
    ('POST', '/api/submit_homework_problem/'),
    ('GET', '/api/homework_comments/'),
    
    # Admin endpoints
    ('GET', '/api/admin_homework_list/'),
    ('POST', '/api/admin_create_homework/'),
    ('DELETE', '/api/admin_delete_homework/'),
    ('GET', '/api/available_students/'),
    
    # Debug endpoint
    ('GET', '/api/homework_debug/'),
]

print("Testing homework endpoints...")
print("-" * 50)

for method, url in test_endpoints:
    try:
        match = resolve(url)
        print(f"✓ {method} {url} -> {match.func.__name__}")
    except Exception as e:
        print(f"✗ {method} {url} -> ERROR: {e}")

# Also print all URLs that contain 'homework'
print("\n" + "-" * 50)
print("All registered homework-related URLs:")
print("-" * 50)

from django.urls import get_resolver
resolver = get_resolver()

def get_all_url_patterns(resolver, prefix=''):
    patterns = []
    for pattern in resolver.url_patterns:
        if hasattr(pattern, 'pattern'):
            new_prefix = prefix + str(pattern.pattern)
            if hasattr(pattern, 'url_patterns'):
                # This is an include
                patterns.extend(get_all_url_patterns(pattern, new_prefix))
            else:
                patterns.append(new_prefix)
    return patterns

all_patterns = get_all_url_patterns(resolver)
homework_patterns = [p for p in all_patterns if 'homework' in p or 'student' in p]

for pattern in sorted(homework_patterns):
    print(f"  {pattern}")