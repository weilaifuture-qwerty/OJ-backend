#!/usr/bin/env python3
"""Check actual problem ID"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj.settings')
django.setup()

from problem.models import Problem

# Find all problems
problems = Problem.objects.all()
print(f"Total problems: {problems.count()}")
print()

for p in problems:
    print(f"Problem:")
    print(f"  id (PK): {p.id}")
    print(f"  _id (display): {p._id}")
    print(f"  title: {p.title}")
    print(f"  visible: {p.visible}")
    print(f"  contest_id: {p.contest_id}")
    print()