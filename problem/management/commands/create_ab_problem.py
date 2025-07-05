from django.core.management.base import BaseCommand
from django.utils import timezone
from problem.models import Problem, ProblemTag
from account.models import User
import json
import os


class Command(BaseCommand):
    help = 'Creates the A+B problem with test cases'

    def handle(self, *args, **options):
        # Get or create admin user
        admin_user, created = User.objects.get_or_create(
            username='root',
            defaults={
                'email': 'root@oj.com',
                'admin_type': 'SUPER_ADMIN',
                'is_disabled': False
            }
        )
        
        if created:
            admin_user.set_password('rootroot')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Created admin user: root'))

        # Create A+B Problem
        problem_data = {
            "_id": "1",
            "title": "A+B Problem",
            "description": "<p>Calculate the sum of two integers A and B.</p>",
            "input_description": "<p>Two integers A and B separated by a space. (-10^9 ≤ A, B ≤ 10^9)</p>",
            "output_description": "<p>Output the sum of A and B.</p>",
            "samples": json.dumps([
                {"input": "1 2", "output": "3"},
                {"input": "10 20", "output": "30"}
            ]),
            "test_case_id": "ab_problem_test",
            "test_case_score": json.dumps([
                {"score": 10, "input_name": f"{i}.in", "output_name": f"{i}.out"}
                for i in range(1, 11)
            ]),
            "hint": "<p>This is a simple problem to test your programming environment.</p>",
            "languages": ["C", "C++", "Java", "Python2", "Python3"],
            "template": {},
            "create_time": timezone.now(),
            "created_by": admin_user,
            "time_limit": 1000,
            "memory_limit": 256,
            "io_mode": {"input": "stdin", "output": "stdout"},
            "spj": False,
            "rule_type": "ACM",
            "visible": True,
            "difficulty": "Low",
            "source": "Classic",
            "total_score": 100,
            "submission_number": 0,
            "accepted_number": 0,
            "statistic_info": {}
        }

        problem, created = Problem.objects.update_or_create(
            _id="1",
            defaults=problem_data
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created problem: {problem.title}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated problem: {problem.title}'))

        # Add tags
        tag, _ = ProblemTag.objects.get_or_create(name="beginner")
        problem.tags.add(tag)

        # Create test cases
        test_cases = [
            ("1 2", "3"),
            ("10 20", "30"),
            ("100 200", "300"),
            ("-5 5", "0"),
            ("999 1", "1000"),
            ("0 0", "0"),
            ("-10 -20", "-30"),
            ("12345 54321", "66666"),
            ("1000000 2000000", "3000000"),
            ("-1000 1000", "0")
        ]

        # Create test case directory
        test_case_dir = os.path.join('data', 'test_case', 'ab_problem_test')
        os.makedirs(test_case_dir, exist_ok=True)

        for i, (input_data, output_data) in enumerate(test_cases, 1):
            # Input file
            with open(os.path.join(test_case_dir, f'{i}.in'), 'w') as f:
                f.write(input_data + '\n')
            
            # Output file
            with open(os.path.join(test_case_dir, f'{i}.out'), 'w') as f:
                f.write(output_data + '\n')

        self.stdout.write(self.style.SUCCESS(f'Created {len(test_cases)} test cases'))
        self.stdout.write(self.style.SUCCESS('\nA+B Problem created successfully!'))
        self.stdout.write('\nYou can now:')
        self.stdout.write('1. Login as root/rootroot')
        self.stdout.write('2. Go to Problems section')
        self.stdout.write('3. Submit a solution to A+B Problem')