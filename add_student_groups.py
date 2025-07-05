#!/usr/bin/env python
"""
Quick script to add groups to existing students
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj.settings')
django.setup()

from account.models import User, UserProfile, AdminType

def add_groups():
    groups = ["Class A", "Class B", "Class C", "Advanced", "Beginners"]
    
    # Get all students
    students = User.objects.filter(admin_type=AdminType.REGULAR_USER)
    print(f"Found {students.count()} students")
    
    updated = 0
    for i, student in enumerate(students):
        profile, created = UserProfile.objects.get_or_create(user=student)
        if not profile.student_group:
            profile.student_group = groups[i % len(groups)]
            profile.save()
            updated += 1
            print(f"Added {student.username} to {profile.student_group}")
        else:
            print(f"{student.username} already in {profile.student_group}")
    
    print(f"\nUpdated {updated} students with groups")
    
    # Show group distribution
    print("\nGroup Distribution:")
    for group in groups:
        count = UserProfile.objects.filter(
            user__admin_type=AdminType.REGULAR_USER,
            student_group=group
        ).count()
        print(f"  {group}: {count} students")

if __name__ == "__main__":
    add_groups()