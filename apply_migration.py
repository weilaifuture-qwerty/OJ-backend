#!/usr/bin/env python
"""
Apply a specific migration
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj.settings')

print("Setting up Django...")
django.setup()

from django.core.management import execute_from_command_line

print("\nApplying homework migration 0002_add_auto_grade...")
execute_from_command_line(['manage.py', 'migrate', 'homework', '0002_add_auto_grade'])

print("\nMigration applied!")