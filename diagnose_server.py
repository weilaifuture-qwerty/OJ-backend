#!/usr/bin/env python
"""
Diagnose server issues
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj.settings')

print("Checking Django setup...")
try:
    django.setup()
    print("✓ Django setup successful")
except Exception as e:
    print(f"✗ Django setup failed: {e}")
    sys.exit(1)

# Check imports
print("\nChecking imports...")
try:
    from account.models import User, AdminType
    print("✓ Account models imported")
except Exception as e:
    print(f"✗ Account models import failed: {e}")

try:
    from homework.models import HomeworkAssignment
    print("✓ Homework models imported")
except Exception as e:
    print(f"✗ Homework models import failed: {e}")

try:
    from problem.models import Problem
    print("✓ Problem models imported")
except Exception as e:
    print(f"✗ Problem models import failed: {e}")

# Check database
print("\nChecking database...")
try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        print("✓ Database connection successful")
except Exception as e:
    print(f"✗ Database connection failed: {e}")

# Check migrations
print("\nChecking for pending migrations...")
try:
    from django.core.management import call_command
    from io import StringIO
    import sys
    
    # Capture output
    out = StringIO()
    call_command('showmigrations', '--plan', stdout=out)
    output = out.getvalue()
    
    if '[ ]' in output:
        print("✗ There are unapplied migrations!")
        print("Run: python manage.py migrate")
    else:
        print("✓ All migrations applied")
except Exception as e:
    print(f"✗ Migration check failed: {e}")

# Test basic API
print("\nTesting basic API endpoint...")
try:
    from utils.api import APIView
    print("✓ APIView imported successfully")
    
    # Check if server_error method exists
    if hasattr(APIView, 'server_error'):
        print("✓ server_error method exists")
    else:
        print("✗ server_error method missing")
except Exception as e:
    print(f"✗ APIView import failed: {e}")

# Check for syntax errors in views
print("\nChecking view files for syntax errors...")
view_files = [
    'account/views/oj.py',
    'homework/views/admin.py',
    'homework/views/oj.py',
    'conf/views.py'
]

for view_file in view_files:
    try:
        with open(view_file, 'r') as f:
            code = f.read()
        compile(code, view_file, 'exec')
        print(f"✓ {view_file} - No syntax errors")
    except SyntaxError as e:
        print(f"✗ {view_file} - Syntax error: {e}")
    except FileNotFoundError:
        print(f"? {view_file} - File not found")
    except Exception as e:
        print(f"✗ {view_file} - Error: {e}")

print("\n" + "="*60)
print("DIAGNOSIS COMPLETE")
print("="*60)