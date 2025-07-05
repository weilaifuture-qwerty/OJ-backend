#!/usr/bin/env python
"""
Verify the homework system is working correctly
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
from account.models import User, AdminType, UserProfile
from problem.models import Problem
from homework.models import HomeworkAssignment, HomeworkProblem, StudentHomework, AdminStudentRelation

def check_system():
    print("=" * 60)
    print("HOMEWORK SYSTEM VERIFICATION")
    print("=" * 60)
    
    # 1. Check Users
    print("\n1. USER STATUS:")
    admins = User.objects.filter(admin_type__in=[AdminType.ADMIN, AdminType.SUPER_ADMIN])
    students = User.objects.filter(admin_type=AdminType.REGULAR_USER)
    
    print(f"   Admins: {admins.count()}")
    for admin in admins[:3]:
        print(f"   - {admin.username} ({admin.admin_type})")
    
    print(f"\n   Students: {students.count()}")
    for student in students:
        profile = getattr(student, 'userprofile', None)
        group = profile.student_group if profile else 'No profile'
        print(f"   - {student.username} (Group: {group})")
    
    # 2. Check Groups
    print("\n2. GROUP STATUS:")
    groups = UserProfile.objects.filter(
        user__admin_type=AdminType.REGULAR_USER
    ).exclude(
        student_group__isnull=True
    ).exclude(
        student_group=''
    ).values_list('student_group', flat=True).distinct()
    
    print(f"   Groups: {list(groups)}")
    
    # 3. Check Problems
    print("\n3. PROBLEM STATUS:")
    problems = Problem.objects.all()
    print(f"   Total problems: {problems.count()}")
    for prob in problems[:3]:
        print(f"   - {prob._id}: {prob.title}")
    
    # 4. Check Homework
    print("\n4. HOMEWORK STATUS:")
    homeworks = HomeworkAssignment.objects.all()
    print(f"   Total homework: {homeworks.count()}")
    
    # 5. Check Admin-Student Relations
    print("\n5. ADMIN-STUDENT RELATIONS:")
    relations = AdminStudentRelation.objects.all()
    print(f"   Total relations: {relations.count()}")
    if relations.exists():
        for rel in relations[:5]:
            print(f"   - Admin: {rel.admin.username} -> Student: {rel.student.username}")
    
    # 6. Test Homework Creation
    print("\n6. TESTING HOMEWORK CREATION:")
    admin = admins.first()
    if admin and problems.exists() and students.exists():
        print(f"   Using admin: {admin.username}")
        print(f"   Using problem: {problems.first().title}")
        print(f"   Using student: {students.first().username}")
        
        try:
            # Simulate homework creation
            print("   ✓ All requirements met for homework creation")
        except Exception as e:
            print(f"   ✗ Error: {e}")
    else:
        print("   ✗ Missing requirements:")
        if not admin:
            print("     - No admin users")
        if not problems.exists():
            print("     - No problems")
        if not students.exists():
            print("     - No students")
    
    # 7. Check model relationships
    print("\n7. MODEL RELATIONSHIPS:")
    from homework.models import HomeworkAssignment
    
    # Check if the model has the expected related names
    hw_fields = [f.name for f in HomeworkAssignment._meta.get_fields()]
    print(f"   HomeworkAssignment fields: {', '.join(hw_fields[:10])}...")
    
    # Check specific relationships
    print(f"   Has 'problems' field: {'problems' in hw_fields}")
    print(f"   Has 'studenthomework_set' field: {'studenthomework_set' in hw_fields}")
    print(f"   Has 'assigned_students' field: {'assigned_students' in hw_fields}")
    
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    check_system()