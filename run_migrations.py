#!/usr/bin/env python
"""
Run migrations for the homework app
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj.settings')

print("Setting up Django...")
django.setup()

# Run migrations
from django.core.management import execute_from_command_line

print("\nCreating migrations for homework app...")
execute_from_command_line(['manage.py', 'makemigrations', 'homework'])

print("\nShowing migrations...")
execute_from_command_line(['manage.py', 'showmigrations', 'homework'])

print("\nApplying migrations...")
execute_from_command_line(['manage.py', 'migrate'])

print("\nMigrations complete!")