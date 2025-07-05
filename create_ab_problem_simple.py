#!/usr/bin/env python3
"""Simple script to create A+B problem using Django shell"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj.settings')
django.setup()

from problem.models import Problem, ProblemTag
from account.models import User
import json
import hashlib
import shutil

def create_ab_problem():
    """Create A+B problem in database"""
    print("Creating A+B Problem...")
    
    # Get admin user
    try:
        admin = User.objects.get(username="root")
    except User.DoesNotExist:
        print("Error: Admin user 'root' not found!")
        return False
    
    # Check if problem already exists
    if Problem.objects.filter(_id="1").exists():
        print("A+B problem already exists!")
        return True
    
    # Create test case directory
    test_case_id = "ab_problem_test"
    test_case_dir = f"data/test_case/{test_case_id}"
    os.makedirs(test_case_dir, exist_ok=True)
    
    # Create test cases
    test_cases = [
        ("1 2", "3"),
        ("10 20", "30"),
        ("100 200", "300"),
        ("-5 5", "0"),
        ("999 1", "1000"),
    ]
    
    for i, (input_data, output_data) in enumerate(test_cases, 1):
        # Write input file
        with open(f"{test_case_dir}/{i}.in", 'w') as f:
            f.write(input_data + '\n')
        
        # Write output file
        with open(f"{test_case_dir}/{i}.out", 'w') as f:
            f.write(output_data + '\n')
    
    print(f"Created {len(test_cases)} test cases")
    
    # Create info file
    info = {
        "test_case_number": len(test_cases),
        "spj": False,
        "test_cases": {}
    }
    
    for i in range(1, len(test_cases) + 1):
        # Get file sizes
        input_size = os.path.getsize(f"{test_case_dir}/{i}.in")
        output_size = os.path.getsize(f"{test_case_dir}/{i}.out")
        
        # Calculate MD5
        with open(f"{test_case_dir}/{i}.in", 'rb') as f:
            input_md5 = hashlib.md5(f.read()).hexdigest()
        with open(f"{test_case_dir}/{i}.out", 'rb') as f:
            output_md5 = hashlib.md5(f.read()).hexdigest()
        
        info["test_cases"][str(i)] = {
            "input_size": input_size,
            "output_size": output_size,
            "input_name": f"{i}.in",
            "output_name": f"{i}.out",
            "input_md5": input_md5,
            "output_md5": output_md5
        }
    
    with open(f"{test_case_dir}/info", 'w') as f:
        json.dump(info, f, indent=2)
    
    # Create problem
    problem = Problem.objects.create(
        _id="1",
        title="A+B Problem",
        description="<p>Calculate the sum of two integers.</p>\n"
                   "<p>Given two integers A and B, output their sum A+B.</p>",
        input_description="<p>Two integers A and B separated by a space.</p>\n"
                         "<p>(-1000 ≤ A, B ≤ 1000)</p>",
        output_description="<p>Output a single integer, the sum of A and B.</p>",
        samples=[
            {"input": "1 2", "output": "3"},
            {"input": "10 20", "output": "30"}
        ],
        test_case_id=test_case_id,
        test_case_score=[],
        time_limit=1000,  # 1 second
        memory_limit=256,  # 256 MB
        difficulty="Low",
        source="Classic",
        languages=["C", "C++", "Java", "Python2", "Python3"],
        template={},
        created_by=admin,
        visible=True,
        total_score=100,
        submission_number=0,
        accepted_number=0,
        statistic_info={
            "0": 0,  # AC
            "1": 0,  # TLE
            "2": 0,  # TLE  
            "3": 0,  # MLE
            "4": 0,  # RE
            "5": 0,  # SE
            "6": 0,  # CE
            "-1": 0, # WA
            "-2": 0  # Pending
        }
    )
    
    print(f"✓ Created problem: {problem.title} (ID: {problem._id})")
    print(f"  Test cases: {len(test_cases)}")
    print(f"  Time limit: {problem.time_limit}ms")
    print(f"  Memory limit: {problem.memory_limit}MB")
    
    return True


if __name__ == "__main__":
    if create_ab_problem():
        print("\n✓ A+B problem created successfully!")
        print("You can now test submissions.")
    else:
        print("\n✗ Failed to create A+B problem")