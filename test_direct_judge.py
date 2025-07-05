#!/usr/bin/env python3
"""Test judge dispatcher directly"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj.settings')
django.setup()

from submission.models import Submission
from judge.dispatcher import JudgeDispatcher

def test_direct_judge():
    """Test judge dispatcher directly"""
    print("Testing direct judge...")
    
    # Get the latest submission
    submission = Submission.objects.order_by('-create_time').first()
    if not submission:
        print("No submissions found!")
        return
    
    print(f"\nLatest submission:")
    print(f"  ID: {submission.id}")
    print(f"  Problem ID: {submission.problem_id}")
    print(f"  Language: {submission.language}")
    print(f"  Result: {submission.result}")
    print(f"  Code: {submission.code[:50]}...")
    
    if submission.result == -2:  # Pending
        print("\nTrying to judge directly...")
        try:
            # Judge directly without async
            dispatcher = JudgeDispatcher(submission.id, submission.problem_id)
            dispatcher.judge()
            print("✓ Judge dispatched")
            
            # Reload submission
            submission.refresh_from_db()
            print(f"\nNew result: {submission.result}")
            if submission.result == 6:  # Compile error
                print(f"Compile error info: {submission.statistic_info}")
        except Exception as e:
            print(f"✗ Judge failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Submission already judged")


if __name__ == "__main__":
    test_direct_judge()