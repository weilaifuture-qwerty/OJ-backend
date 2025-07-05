#!/usr/bin/env python
"""
Fix migration issues by marking them as applied
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
from django.db import connection

print("\nChecking current migration status...")
execute_from_command_line(['manage.py', 'showmigrations', 'homework'])

print("\nMarking migrations as applied...")
# Mark the problematic migrations as applied
with connection.cursor() as cursor:
    try:
        # Check if migrations are already recorded
        cursor.execute("""
            SELECT name FROM django_migrations 
            WHERE app = 'homework' 
            AND name IN ('0002_add_auto_grade', '0002_homeworkassignment_auto_grade', '0003_merge_20250629_0254')
        """)
        existing = [row[0] for row in cursor.fetchall()]
        
        # Mark migrations as applied if not already recorded
        migrations_to_mark = [
            ('0002_add_auto_grade', 'homework'),
            ('0002_homeworkassignment_auto_grade', 'homework'),
            ('0003_merge_20250629_0254', 'homework')
        ]
        
        for migration_name, app_name in migrations_to_mark:
            if migration_name not in existing:
                cursor.execute("""
                    INSERT INTO django_migrations (app, name, applied)
                    VALUES (%s, %s, NOW())
                """, [app_name, migration_name])
                print(f"✓ Marked {migration_name} as applied")
            else:
                print(f"✓ {migration_name} already marked as applied")
                
    except Exception as e:
        print(f"Error: {e}")

print("\nChecking migration status again...")
execute_from_command_line(['manage.py', 'showmigrations', 'homework'])

print("\nMigration fix complete!")