#!/usr/bin/env python
"""
Test homework creation to identify the exact error
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
from django.db import transaction
from account.models import User, AdminType
from problem.models import Problem
from homework.models import HomeworkAssignment, HomeworkProblem, StudentHomework

def test_create_homework():
    print("Testing homework creation...")
    print("=" * 60)
    
    # Get admin user
    admin = User.objects.filter(admin_type=AdminType.SUPER_ADMIN).first()
    if not admin:
        admin = User.objects.filter(admin_type=AdminType.ADMIN).first()
    
    print(f"Admin user: {admin.username if admin else 'None'}")
    
    # Get problem with ID 3
    problem = Problem.objects.filter(id=3).first()
    print(f"Problem ID 3: {problem.title if problem else 'Not found'}")
    
    # Get student with ID 11
    student = User.objects.filter(id=11).first()
    print(f"Student ID 11: {student.username if student else 'Not found'} (type: {student.admin_type if student else 'N/A'})")
    
    if not all([admin, problem, student]):
        print("\nMissing required data!")
        return
    
    # Simulate the exact data from frontend
    data = {
        'title': 'hi',
        'description': 'Complete the assigned problems by the due date.',
        'due_date': timezone.now() + timedelta(days=1),
        'problem_ids': [3],
        'student_ids': [11],
        'auto_grade': True
    }
    
    print("\nTrying to create homework...")
    
    try:
        with transaction.atomic():
            # Create homework assignment
            homework = HomeworkAssignment.objects.create(
                title=data['title'],
                description=data['description'],
                created_by=admin,
                due_date=data['due_date'],
                allow_late_submission=data.get('allow_late_submission', False),
                late_penalty_percent=data.get('late_penalty_percent', 0),
                max_attempts=data.get('max_attempts', 0),
                auto_grade=data.get('auto_grade', True)
            )
            print(f"✓ Created homework: {homework.id}")
            
            # Add problems to homework
            for idx, problem_id in enumerate(data['problem_ids']):
                hp = HomeworkProblem.objects.create(
                    homework=homework,
                    problem_id=problem_id,
                    order=idx,
                    points=100,
                    required=True
                )
                print(f"✓ Added problem {problem_id} to homework")
            
            # Assign to students
            student_ids = data.get('student_ids', [])
            
            if admin.admin_type == AdminType.SUPER_ADMIN:
                print("Admin is SUPER_ADMIN")
                for student_id in student_ids:
                    if User.objects.filter(id=student_id, admin_type=AdminType.REGULAR_USER).exists():
                        sh = StudentHomework.objects.create(
                            student_id=student_id,
                            homework=homework
                        )
                        print(f"✓ Assigned homework to student {student_id}")
                    else:
                        print(f"✗ Student {student_id} not found or not a regular user")
            
        print("\n✓ Homework created successfully!")
        
    except Exception as e:
        print(f"\n✗ Error creating homework: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_create_homework()