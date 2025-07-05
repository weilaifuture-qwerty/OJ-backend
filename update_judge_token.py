#!/usr/bin/env python3
"""Update judge server token to match docker container"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj.settings')
django.setup()

from options.options import SysOptions

def update_token():
    """Update judge server token"""
    print("Updating judge server token...")
    
    old_token = SysOptions.judge_server_token
    new_token = "CHANGE_THIS_TOKEN"
    
    print(f"Old token: {old_token}")
    print(f"New token: {new_token}")
    
    SysOptions.judge_server_token = new_token
    
    print("✓ Token updated successfully!")
    
    # Test with curl
    print("\nTesting judge server with new token...")
    import subprocess
    
    result = subprocess.run([
        "curl", "-s", "-X", "POST", "http://localhost:12358/judge",
        "-H", "Content-Type: application/json",
        "-H", f"X-Judge-Server-Token: {new_token}",
        "-d", '{"src": "print(1+1)", "language_config": {"compile": {"src_name": "solution.py", "exe_name": "solution.pyc", "max_cpu_time": 3000, "max_real_time": 5000, "max_memory": 134217728, "compile_command": "/usr/bin/python3 -m py_compile {src_path}"}, "run": {"command": "/usr/bin/python3 {exe_path}", "seccomp_rule": "general", "env": ["PYTHONIOENCODING=UTF-8"]}}, "max_cpu_time": 1000, "max_memory": 134217728, "test_case_id": "ab_problem_test", "output": true}'
    ], capture_output=True, text=True)
    
    print(f"Response: {result.stdout}")
    
    return True


if __name__ == "__main__":
    if update_token():
        print("\n✓ Judge server token updated!")
    else:
        print("\n✗ Failed to update token")