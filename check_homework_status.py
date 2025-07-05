#!/usr/bin/env python
"""
Check homework system status
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj.settings')

print("Setting up Django...")
django.setup()

from django.db import connection
from account.models import User, AdminType
from homework.models import HomeworkAssignment, HomeworkProblem, StudentHomework
from problem.models import Problem

print("\n=== CHECKING HOMEWORK SYSTEM STATUS ===\n")

# Check database tables
print("1. Checking database tables...")
with connection.cursor() as cursor:
    # Check if homework tables exist
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE 'homework_%'
    """)
    tables = cursor.fetchall()
    print(f"Found {len(tables)} homework tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check homework_assignment columns
    print("\n2. Checking homework_assignment columns...")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'homework_assignment'
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    for col in columns:
        print(f"  - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")

# Check users
print("\n3. Checking users...")
admins = User.objects.filter(admin_type__in=[AdminType.ADMIN, AdminType.SUPER_ADMIN])
students = User.objects.filter(admin_type=AdminType.REGULAR_USER)
print(f"  - Admins: {admins.count()}")
print(f"  - Students: {students.count()}")

# Check student groups
print("\n4. Checking student groups...")
from account.models import UserProfile
groups = UserProfile.objects.exclude(student_group__isnull=True).exclude(student_group='').values('student_group').distinct()
for group in groups:
    count = UserProfile.objects.filter(student_group=group['student_group']).count()
    print(f"  - {group['student_group']}: {count} students")

# Check problems
print("\n5. Checking problems...")
problems = Problem.objects.all()
print(f"  - Total problems: {problems.count()}")

# Check homework
print("\n6. Checking homework assignments...")
homework = HomeworkAssignment.objects.all()
print(f"  - Total homework: {homework.count()}")

# Test creating a simple homework
print("\n7. Testing homework creation...")
try:
    # Get first admin
    admin = admins.first()
    if admin:
        print(f"  - Using admin: {admin.username}")
        
        # Get first problem
        problem = problems.first()
        if problem:
            print(f"  - Using problem: {problem.title}")
            
            # Try to create test homework
            from django.utils import timezone
            from datetime import timedelta
            
            test_hw = HomeworkAssignment.objects.create(
                title="Test Homework (Diagnostic)",
                description="Test homework created by diagnostic script",
                created_by=admin,
                due_date=timezone.now() + timedelta(days=7),
                allow_late_submission=True,
                late_penalty_percent=10,
                max_attempts=0
            )
            print(f"  ✓ Created test homework with ID: {test_hw.id}")
            
            # Add problem
            hw_problem = HomeworkProblem.objects.create(
                homework=test_hw,
                problem=problem,
                order=0,
                points=100,
                required=True
            )
            print(f"  ✓ Added problem to homework")
            
            # Clean up
            test_hw.delete()
            print("  ✓ Cleaned up test homework")
        else:
            print("  ! No problems found")
    else:
        print("  ! No admins found")
        
except Exception as e:
    print(f"  ✗ Error creating test homework: {e}")
    import traceback
    traceback.print_exc()

print("\n=== DIAGNOSTIC COMPLETE ===")