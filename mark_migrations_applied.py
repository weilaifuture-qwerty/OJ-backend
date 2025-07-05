#!/usr/bin/env python
"""
Mark migrations as applied since the column already exists
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj.settings')

print("Setting up Django...")
django.setup()

from django.core.management import call_command

print("\nMarking migration 0002_homeworkassignment_auto_grade as applied...")
try:
    # Use --fake to mark the migration as applied without running it
    call_command('migrate', 'homework', '0002_homeworkassignment_auto_grade', '--fake')
    print("✓ Migration marked as applied")
except Exception as e:
    print(f"Error: {e}")

print("\nChecking migration status...")
call_command('showmigrations', 'homework')

print("\nDone!")