#!/usr/bin/env python3
"""Create A+B Problem with test cases"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oj.settings")
django.setup()

from problem.models import Problem, ProblemTag
from account.models import User
from django.utils import timezone
import json

def create_ab_problem():
    """Create the classic A+B problem"""
    
    # Get admin user (assuming username 'root' exists)
    try:
        admin_user = User.objects.get(username='root')
    except User.DoesNotExist:
        print("Admin user 'root' not found. Please create an admin user first.")
        return
    
    # Define test cases for A+B problem
    test_cases = [
        {
            "input": "1 2\n",
            "output": "3\n"
        },
        {
            "input": "10 20\n",
            "output": "30\n"
        },
        {
            "input": "100 200\n",
            "output": "300\n"
        },
        {
            "input": "-5 5\n",
            "output": "0\n"
        },
        {
            "input": "999 1\n",
            "output": "1000\n"
        },
        {
            "input": "0 0\n",
            "output": "0\n"
        },
        {
            "input": "-10 -20\n",
            "output": "-30\n"
        },
        {
            "input": "12345 54321\n",
            "output": "66666\n"
        },
        {
            "input": "1000000 2000000\n",
            "output": "3000000\n"
        },
        {
            "input": "-1000 1000\n",
            "output": "0\n"
        }
    ]
    
    # Problem details
    problem_data = {
        "_id": "1",  # Custom problem ID
        "title": "A+B Problem",
        "description": """<p>Calculate the sum of two integers A and B.</p>

<p>This is the most basic problem to test if your environment is working correctly.</p>""",
        "input_description": """<p>The input consists of a single line containing two integers A and B, separated by a space.</p>

<p>Constraints:</p>
<ul>
<li>-10<sup>9</sup> ≤ A, B ≤ 10<sup>9</sup></li>
</ul>""",
        "output_description": """<p>Output a single integer - the sum of A and B.</p>""",
        "samples": json.dumps([
            {
                "input": "1 2",
                "output": "3"
            },
            {
                "input": "10 20",
                "output": "30"
            }
        ]),
        "test_case_id": "ab_problem_test",
        "test_case_score": json.dumps([
            {"score": 10, "input_name": "1.in", "output_name": "1.out"},
            {"score": 10, "input_name": "2.in", "output_name": "2.out"},
            {"score": 10, "input_name": "3.in", "output_name": "3.out"},
            {"score": 10, "input_name": "4.in", "output_name": "4.out"},
            {"score": 10, "input_name": "5.in", "output_name": "5.out"},
            {"score": 10, "input_name": "6.in", "output_name": "6.out"},
            {"score": 10, "input_name": "7.in", "output_name": "7.out"},
            {"score": 10, "input_name": "8.in", "output_name": "8.out"},
            {"score": 10, "input_name": "9.in", "output_name": "9.out"},
            {"score": 10, "input_name": "10.in", "output_name": "10.out"}
        ]),
        "hint": """<p>Example solutions:</p>

<p><strong>Python:</strong></p>
<pre><code>a, b = map(int, input().split())
print(a + b)</code></pre>

<p><strong>C++:</strong></p>
<pre><code>#include &lt;iostream&gt;
using namespace std;

int main() {
    int a, b;
    cin >> a >> b;
    cout << a + b << endl;
    return 0;
}</code></pre>

<p><strong>Java:</strong></p>
<pre><code>import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int a = sc.nextInt();
        int b = sc.nextInt();
        System.out.println(a + b);
    }
}</code></pre>""",
        "languages": ["C", "C++", "Java", "Python2", "Python3", "JavaScript", "Go"],
        "template": {},  # Language templates can be added here
        "create_time": timezone.now(),
        "last_update_time": None,
        "created_by": admin_user,
        "time_limit": 1000,  # 1 second
        "memory_limit": 256,  # 256 MB
        "io_mode": {"input": "stdin", "output": "stdout"},
        "spj": False,  # No special judge needed
        "spj_language": None,
        "spj_code": None,
        "spj_version": None,
        "rule_type": "ACM",
        "visible": True,
        "difficulty": "Low",
        "source": "Classic Problem",
        "total_score": 100,
        "submission_number": 0,
        "accepted_number": 0,
        "statistic_info": {}
    }
    
    # Check if problem already exists
    if Problem.objects.filter(_id="1").exists():
        print("Problem with ID '1' already exists. Updating...")
        problem = Problem.objects.get(_id="1")
        for key, value in problem_data.items():
            setattr(problem, key, value)
        problem.save()
    else:
        print("Creating new A+B problem...")
        problem = Problem.objects.create(**problem_data)
    
    # Add tags
    tag_names = ["beginner", "implementation", "arithmetic"]
    for tag_name in tag_names:
        tag, created = ProblemTag.objects.get_or_create(name=tag_name)
        problem.tags.add(tag)
    
    print(f"Problem '{problem.title}' created/updated successfully!")
    print(f"Problem ID: {problem._id}")
    
    # Create test case directory
    test_case_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data",
        "test_case",
        problem_data["test_case_id"]
    )
    
    os.makedirs(test_case_dir, exist_ok=True)
    
    # Write test cases to files
    print(f"\nCreating test cases in {test_case_dir}...")
    for i, test_case in enumerate(test_cases, 1):
        # Write input file
        input_file = os.path.join(test_case_dir, f"{i}.in")
        with open(input_file, 'w') as f:
            f.write(test_case["input"])
        
        # Write output file
        output_file = os.path.join(test_case_dir, f"{i}.out")
        with open(output_file, 'w') as f:
            f.write(test_case["output"])
        
        print(f"Created test case {i}: {test_case['input'].strip()} -> {test_case['output'].strip()}")
    
    # Create info file for test cases
    info = {
        "spj": False,
        "test_cases": {
            f"{i}": {
                "stripped_output_md5": "",  # Will be calculated by judge
                "output_size": len(test_cases[i-1]["output"]),
                "input_name": f"{i}.in",
                "input_size": len(test_cases[i-1]["input"]),
                "output_name": f"{i}.out"
            } for i in range(1, len(test_cases) + 1)
        }
    }
    
    info_file = os.path.join(test_case_dir, "info")
    with open(info_file, 'w') as f:
        json.dump(info, f, indent=2)
    
    print(f"\nTest cases created successfully!")
    print(f"Total test cases: {len(test_cases)}")
    
    # Create a simple solution file for reference
    solution_file = os.path.join(test_case_dir, "solution.py")
    with open(solution_file, 'w') as f:
        f.write("a, b = map(int, input().split())\nprint(a + b)\n")
    
    print(f"\nSample solution saved at: {solution_file}")
    
    print("\n✅ A+B Problem setup complete!")
    print("\nNext steps:")
    print("1. Start the Django server: python manage.py runserver")
    print("2. Login as admin")
    print("3. Go to Problems section")
    print("4. You should see 'A+B Problem' in the list")
    print("5. Try submitting a solution!")
    
    # Test the test cases with the solution
    print("\n📝 Testing the solution against test cases...")
    for i, test_case in enumerate(test_cases, 1):
        a, b = map(int, test_case["input"].strip().split())
        expected = int(test_case["output"].strip())
        result = a + b
        status = "✅" if result == expected else "❌"
        print(f"Test {i}: {a} + {b} = {result} {status}")


if __name__ == "__main__":
    create_ab_problem()