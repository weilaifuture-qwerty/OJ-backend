#!/usr/bin/env python
"""
Check if migrations are needed
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

print("Checking migrations...")
print("=" * 60)

# Check for unapplied migrations
try:
    call_command('showmigrations', '--plan', verbosity=0)
except:
    pass

# Check if homework tables exist
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE 'homework_%'
        ORDER BY name;
    """)
    tables = cursor.fetchall()
    
    print("\nHomework tables in database:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check if the problems relationship exists
    try:
        cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='homework_homeworkproblem';
        """)
        result = cursor.fetchone()
        if result:
            print(f"\nHomeworkProblem table schema:\n{result[0]}")
    except:
        print("\nCouldn't check HomeworkProblem table schema")

print("\nRun 'python manage.py makemigrations' if you see any issues above.")