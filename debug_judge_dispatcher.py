#!/usr/bin/env python3
"""Debug judge dispatcher"""

import os
import sys
import django
import logging

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj.settings')
django.setup()

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

from submission.models import Submission
from judge.dispatcher import JudgeDispatcher
from problem.models import Problem

def debug_judge():
    """Debug judge process"""
    print("Debug judge dispatcher...")
    
    # Get problem
    problem = Problem.objects.get(_id="1")
    print(f"Problem: {problem.title} (ID: {problem.id})")
    print(f"Test case ID: {problem.test_case_id}")
    
    # Create a simple submission
    from account.models import User
    user = User.objects.get(username="root")
    
    submission = Submission.objects.create(
        user_id=user.id,
        username=user.username,
        language="Python3",
        code="print(1+1)",  # Simplest possible code
        problem_id=problem.id,
        ip="127.0.0.1"
    )
    print(f"\nCreated submission: {submission.id}")
    
    # Try to judge with debug info
    print("\nJudging...")
    try:
        dispatcher = JudgeDispatcher(submission.id, problem.id)
        print(f"Token hash: {dispatcher.token}")
        
        # Call judge
        dispatcher.judge()
        
        # Check result
        submission.refresh_from_db()
        print(f"\nResult: {submission.result}")
        print(f"Info: {submission.info}")
        print(f"Statistic info: {submission.statistic_info}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_judge()