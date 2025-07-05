#!/usr/bin/env python
"""
Quick script to check and populate student data with groups
Run this with: python check_data.py
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj.settings')
django.setup()

from account.models import User, UserProfile, AdminType
from django.db.models import Count

def check_data():
    print("Checking student data...")
    print("=" * 50)
    
    # Count students
    total_students = User.objects.filter(admin_type=AdminType.REGULAR_USER).count()
    print(f"Total students: {total_students}")
    
    # Count students with groups
    students_with_groups = UserProfile.objects.filter(
        user__admin_type=AdminType.REGULAR_USER,
        student_group__isnull=False
    ).exclude(student_group='').count()
    print(f"Students with groups: {students_with_groups}")
    print(f"Students without groups: {total_students - students_with_groups}")
    
    # Show group distribution
    print("\nGroup Distribution:")
    groups = UserProfile.objects.filter(
        user__admin_type=AdminType.REGULAR_USER
    ).exclude(
        student_group__isnull=True
    ).exclude(
        student_group=''
    ).values('student_group').annotate(
        count=Count('id')
    ).order_by('student_group')
    
    for group in groups:
        print(f"  {group['student_group']}: {group['count']} students")
    
    if total_students == 0:
        print("\n⚠️  No students found! Creating test data...")
        create_test_data()
    elif students_with_groups == 0:
        print("\n⚠️  Students exist but no groups assigned! Adding groups...")
        add_groups_to_existing()

def create_test_data():
    """Create test students with groups"""
    groups = ["Class A", "Class B", "Class C", "Advanced", "Beginners"]
    
    created = 0
    for i in range(1, 16):
        username = f'student{i}'
        if not User.objects.filter(username=username).exists():
            user = User.objects.create(
                username=username,
                email=f'{username}@example.com',
                admin_type=AdminType.REGULAR_USER
            )
            user.set_password('password123')
            user.save()
            
            UserProfile.objects.create(
                user=user,
                real_name=f'Student {i}',
                student_group=groups[(i-1) % len(groups)]
            )
            created += 1
    
    print(f"✅ Created {created} test students with groups")
    
    # Also create a test admin if none exists
    if not User.objects.filter(admin_type=AdminType.ADMIN).exists():
        admin = User.objects.create(
            username='testadmin',
            email='admin@example.com',
            admin_type=AdminType.ADMIN
        )
        admin.set_password('admin123')
        admin.save()
        UserProfile.objects.create(user=admin, real_name='Test Admin')
        print("✅ Created test admin (username: testadmin, password: admin123)")

def add_groups_to_existing():
    """Add groups to existing students"""
    groups = ["Class A", "Class B", "Class C", "Advanced", "Beginners"]
    students = User.objects.filter(admin_type=AdminType.REGULAR_USER)
    
    updated = 0
    for i, student in enumerate(students):
        profile, created = UserProfile.objects.get_or_create(user=student)
        if not profile.student_group:
            profile.student_group = groups[i % len(groups)]
            profile.save()
            updated += 1
    
    print(f"✅ Updated {updated} students with groups")

if __name__ == "__main__":
    check_data()
    
    print("\n" + "=" * 50)
    print("Data check complete!")
    print("\nNow you can:")
    print("1. Login as admin (testadmin/admin123 if just created)")
    print("2. Visit http://localhost:8080/api/debug_groups to verify data")
    print("3. Try the dropdown again")