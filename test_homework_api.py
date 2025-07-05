#!/usr/bin/env python
"""
Test homework API endpoints
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj.settings')

print("Setting up Django...")
django.setup()

from account.models import User
from homework.models import StudentHomework, HomeworkAssignment

print("\n=== Testing Homework System ===\n")

# Get a student user
student = User.objects.filter(admin_type='REGULAR_USER').first()
if student:
    print(f"Testing with student: {student.username}")
    
    # Check student homework
    student_homework = StudentHomework.objects.filter(student=student)
    print(f"Found {student_homework.count()} homework assignments for this student")
    
    if student_homework.exists():
        sh = student_homework.first()
        print(f"\nFirst homework:")
        print(f"  - ID: {sh.id}")
        print(f"  - Homework ID: {sh.homework.id}")
        print(f"  - Title: {sh.homework.title}")
        print(f"  - Status: {sh.status}")
        
        # Check what the API would return
        print(f"\nFor student_homework_detail API:")
        print(f"  - Should use id={sh.id} (StudentHomework ID)")
        
        print(f"\nFor homework_comments API:")
        print(f"  - Should use homework_id={sh.homework.id} (HomeworkAssignment ID)")
        
else:
    print("No students found")

print("\n=== Test Complete ===")