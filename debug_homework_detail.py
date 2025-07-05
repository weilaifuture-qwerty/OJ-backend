#!/usr/bin/env python
"""
Debug the student homework detail issue
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
from homework.models import StudentHomework, HomeworkProblem
from homework.serializers import StudentHomeworkDetailSerializer

print("\n=== Debugging Student Homework Detail ===\n")

# Get the StudentHomework with ID 4
try:
    sh = StudentHomework.objects.select_related(
        'homework', 'homework__created_by'
    ).get(id=4)
    
    print(f"Found StudentHomework ID 4:")
    print(f"  - Student: {sh.student.username}")
    print(f"  - Homework: {sh.homework.title}")
    print(f"  - Status: {sh.status}")
    print(f"  - Created at: {sh.homework.created_at}")
    print(f"  - Max attempts: {sh.homework.max_attempts}")
    print(f"  - Late penalty: {sh.homework.late_penalty_percent}")
    print(f"  - Feedback: '{sh.feedback}'")
    print(f"  - Total score: {sh.total_score}")
    
    # Check if auto_grade field exists
    try:
        auto_grade = sh.homework.auto_grade
        print(f"  - Auto grade: {auto_grade}")
    except AttributeError:
        print("  - Auto grade field does not exist")
    
    # Check problems
    problems = HomeworkProblem.objects.filter(
        homework=sh.homework
    ).select_related('problem')
    
    print(f"\nProblems ({problems.count()}):")
    for hp in problems:
        print(f"  - {hp.problem.title} (ID: {hp.problem.id}, _id: {hp.problem._id})")
        print(f"    Points: {hp.points}, Order: {hp.order}")
    
    # Try to serialize
    print("\nTrying to serialize...")
    try:
        serializer = StudentHomeworkDetailSerializer(sh)
        data = serializer.data
        print("✓ Serialization successful")
        print(f"Serialized data keys: {list(data.keys())}")
    except Exception as e:
        print(f"✗ Serialization failed: {e}")
        import traceback
        traceback.print_exc()
        
except StudentHomework.DoesNotExist:
    print("StudentHomework with ID 4 not found")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Debug Complete ===")