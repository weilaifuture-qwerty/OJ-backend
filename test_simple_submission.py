#!/usr/bin/env python3
"""Simple test submission and direct judge"""

import os
import sys
import django
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj.settings')
django.setup()

from account.models import User
from problem.models import Problem
from submission.models import Submission
from judge.dispatcher import JudgeDispatcher

def test_submission():
    """Create and judge a submission directly"""
    print("Creating test submission...")
    
    # Get user
    user = User.objects.get(username="root")
    
    # Get problem
    problem = Problem.objects.get(_id="1")  # A+B problem
    print(f"Problem: {problem.title} (ID: {problem.id})")
    
    # Create submission
    submission = Submission.objects.create(
        user_id=user.id,
        username=user.username,
        language="Python3",
        code="a, b = map(int, input().split())\nprint(a + b)",
        problem_id=problem.id,
        ip="127.0.0.1",
        contest_id=None
    )
    print(f"Created submission: {submission.id}")
    
    # Try to judge directly
    print("\nJudging submission...")
    try:
        dispatcher = JudgeDispatcher(submission.id, problem.id)
        dispatcher.judge()
        print("✓ Judge dispatched")
        
        # Wait a bit
        time.sleep(2)
        
        # Check result
        submission.refresh_from_db()
        
        result_map = {
            -2: "Pending",
            -1: "Wrong Answer",
            0: "Accepted",
            1: "CPU Time Limit Exceeded",
            2: "Time Limit Exceeded",
            3: "Memory Limit Exceeded",
            4: "Runtime Error",
            5: "System Error",
            6: "Compile Error",
            7: "Partially Accepted"
        }
        
        print(f"\nResult: {result_map.get(submission.result, 'Unknown')} ({submission.result})")
        
        if submission.result == 6:  # Compile error
            print(f"Compile info: {submission.statistic_info}")
            print(f"Error info: {submission.info}")
        elif submission.result == 0:  # Accepted
            print("✅ SUCCESS! Problem solved correctly!")
            if submission.statistic_info:
                print(f"Time: {submission.statistic_info.get('time_cost', 'N/A')}ms")
                print(f"Memory: {submission.statistic_info.get('memory_cost', 'N/A')}KB")
        
    except Exception as e:
        print(f"✗ Judge failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_submission()