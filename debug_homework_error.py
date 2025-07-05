#!/usr/bin/env python
"""
Debug script to test the homework creation directly
"""

import os
import sys
import django
import json
from datetime import datetime, timedelta

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj.settings')
django.setup()

from django.utils import timezone
from account.models import User, AdminType
from problem.models import Problem
from homework.models import HomeworkAssignment, HomeworkProblem, StudentHomework

def test_homework_creation():
    print("Testing homework creation...")
    
    # Get a superadmin user
    admin = User.objects.filter(admin_type=AdminType.SUPER_ADMIN).first()
    if not admin:
        admin = User.objects.filter(admin_type=AdminType.ADMIN).first()
    
    if not admin:
        print("No admin user found!")
        return
    
    print(f"Using admin: {admin.username} (type: {admin.admin_type})")
    
    # Get a problem
    problem = Problem.objects.first()
    if not problem:
        print("No problems found!")
        return
    
    print(f"Using problem: {problem.title} (ID: {problem.id})")
    
    # Get a student
    student = User.objects.filter(admin_type=AdminType.REGULAR_USER).first()
    if not student:
        print("No students found!")
        return
    
    print(f"Using student: {student.username} (ID: {student.id})")
    
    # Try to create homework
    try:
        # Create homework
        homework = HomeworkAssignment.objects.create(
            title="Test Homework",
            description="Test homework created by debug script",
            created_by=admin,
            due_date=timezone.now() + timedelta(days=7),
            auto_grade=True
        )
        print(f"✅ Created homework: {homework.id}")
        
        # Add problem
        hw_problem = HomeworkProblem.objects.create(
            homework=homework,
            problem=problem,
            order=0,
            points=100,
            required=True
        )
        print(f"✅ Added problem to homework")
        
        # Assign to student
        student_hw = StudentHomework.objects.create(
            student=student,
            homework=homework
        )
        print(f"✅ Assigned homework to student")
        
        print("\nHomework created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating homework: {e}")
        import traceback
        traceback.print_exc()

def check_models():
    print("\nChecking model relationships...")
    
    # Check if models have correct fields
    from homework.models import HomeworkAssignment
    print(f"HomeworkAssignment fields: {[f.name for f in HomeworkAssignment._meta.get_fields()]}")
    
    # Check for any existing homework
    hw_count = HomeworkAssignment.objects.count()
    print(f"Existing homework count: {hw_count}")

if __name__ == "__main__":
    test_homework_creation()
    check_models()