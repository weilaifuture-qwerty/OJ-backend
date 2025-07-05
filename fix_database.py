#!/usr/bin/env python
"""
Fix database by adding missing columns
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj.settings')

print("Setting up Django...")
django.setup()

from django.db import connection

# Add the missing column
with connection.cursor() as cursor:
    try:
        # Check if column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='homework_assignment' 
            AND column_name='auto_grade'
        """)
        
        if not cursor.fetchone():
            print("Adding auto_grade column...")
            cursor.execute("""
                ALTER TABLE homework_assignment 
                ADD COLUMN auto_grade BOOLEAN DEFAULT TRUE
            """)
            print("✓ auto_grade column added successfully")
        else:
            print("✓ auto_grade column already exists")
            
    except Exception as e:
        print(f"Error: {e}")
        # Try alternative approach
        try:
            cursor.execute("""
                ALTER TABLE homework_assignment 
                ADD COLUMN IF NOT EXISTS auto_grade BOOLEAN DEFAULT TRUE
            """)
            print("✓ auto_grade column added successfully (alternative method)")
        except Exception as e2:
            print(f"Alternative method also failed: {e2}")

print("\nDatabase fix complete!")