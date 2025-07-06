# Add this view to problem/views/oj.py

from django.db.models import Q, Max, Count
from account.decorators import login_required
from submission.models import Submission, JudgeStatus
from problem.models import Problem
from utils.api import APIView, validate_serializer
from rest_framework import serializers


class BatchProblemStatusCheckSerializer(serializers.Serializer):
    problem_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100  # Limit to prevent abuse
    )


class BatchProblemStatusAPI(APIView):
    """POST /api/problems/check-status/"""
    @login_required
    @validate_serializer(BatchProblemStatusCheckSerializer)
    def post(self, request):
        problem_ids = request.data.get('problem_ids', [])
        user = request.user
        
        # Get all submissions for these problems by this user
        submissions = Submission.objects.filter(
            user_id=user.id,
            problem_id__in=problem_ids
        ).values('problem_id').annotate(
            accepted=Count('id', filter=Q(result=JudgeStatus.ACCEPTED)),
            total_attempts=Count('id'),
            last_submission=Max('create_time')
        )
        
        # Create a mapping of problem_id to submission stats
        submission_map = {
            sub['problem_id']: sub for sub in submissions
        }
        
        # Get problem details
        problems = Problem.objects.filter(id__in=problem_ids).values(
            'id', '_id', 'title', 'difficulty'
        )
        
        # Build response
        results = []
        for problem in problems:
            problem_id = problem['id']
            submission_data = submission_map.get(problem_id, {})
            
            status = 'not_attempted'
            if submission_data:
                if submission_data['accepted'] > 0:
                    status = 'solved'
                else:
                    status = 'attempted'
            
            results.append({
                'problem_id': problem_id,
                '_id': problem['_id'],
                'title': problem['title'],
                'difficulty': problem['difficulty'],
                'status': status,
                'attempts': submission_data.get('total_attempts', 0),
                'is_accepted': submission_data.get('accepted', 0) > 0,
                'last_submission': submission_data.get('last_submission').isoformat() if submission_data.get('last_submission') else None
            })
        
        # Add entries for non-existent problems
        found_ids = {p['id'] for p in problems}
        for problem_id in problem_ids:
            if problem_id not in found_ids:
                results.append({
                    'problem_id': problem_id,
                    '_id': None,
                    'title': 'Problem not found',
                    'difficulty': None,
                    'status': 'not_found',
                    'attempts': 0,
                    'is_accepted': False,
                    'last_submission': None
                })
        
        return self.success({
            'problems': results,
            'total_checked': len(problem_ids),
            'solved_count': sum(1 for r in results if r['status'] == 'solved'),
            'attempted_count': sum(1 for r in results if r['status'] in ['solved', 'attempted'])
        })