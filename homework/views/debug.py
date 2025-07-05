from utils.api.api import APIView
from account.models import User, AdminType, UserProfile
from problem.models import Problem
from homework.models import HomeworkAssignment, AdminStudentRelation
from django.db import models
import traceback

class DebugHomeworkAPI(APIView):
    """Debug endpoint to check homework system status"""
    
    def get(self, request):
        """Get debug information about homework system"""
        
        try:
            # Check current user
            current_user = {
                'id': request.user.id if request.user.is_authenticated else None,
                'username': request.user.username if request.user.is_authenticated else 'Anonymous',
                'admin_type': request.user.admin_type if request.user.is_authenticated else None,
                'is_authenticated': request.user.is_authenticated
            }
            
            # Count data
            counts = {
                'total_students': User.objects.filter(admin_type=AdminType.REGULAR_USER).count(),
                'total_admins': User.objects.filter(admin_type__in=[AdminType.ADMIN, AdminType.SUPER_ADMIN]).count(),
                'total_problems': Problem.objects.count(),
                'total_homework': HomeworkAssignment.objects.count(),
                'admin_student_relations': AdminStudentRelation.objects.count()
            }
            
            # Check for groups
            groups_info = {
                'unique_groups': list(UserProfile.objects.exclude(
                    student_group__isnull=True
                ).exclude(
                    student_group=''
                ).values_list('student_group', flat=True).distinct()),
                'students_with_groups': UserProfile.objects.filter(
                    user__admin_type=AdminType.REGULAR_USER
                ).exclude(student_group__isnull=True).exclude(student_group='').count()
            }
            
            # Test homework list query
            test_query_error = None
            try:
                if request.user.is_authenticated:
                    homework = HomeworkAssignment.objects.filter(
                        created_by=request.user
                    ).prefetch_related(
                        'homeworkproblem_set__problem',
                        'studenthomework_set__student'
                    ).order_by('-created_at')
                    test_query_result = f"Query successful, found {homework.count()} homework"
                else:
                    test_query_result = "User not authenticated"
            except Exception as e:
                test_query_error = str(e)
                test_query_result = "Query failed"
                traceback.print_exc()
            
            # Check model fields
            model_info = {
                'homework_fields': [f.name for f in HomeworkAssignment._meta.get_fields()],
                'has_studenthomework_set': hasattr(HomeworkAssignment, 'studenthomework_set'),
                'has_problems': hasattr(HomeworkAssignment, 'problems'),
            }
            
            return self.success({
                'current_user': current_user,
                'counts': counts,
                'groups_info': groups_info,
                'test_query': {
                    'result': test_query_result,
                    'error': test_query_error
                },
                'model_info': model_info,
                'endpoints': {
                    'student': [
                        '/api/student_homework',
                        '/api/student_homework_detail',
                        '/api/homework_progress',
                        '/api/submit_homework_problem',
                        '/api/homework_comments'
                    ],
                    'admin': [
                        '/api/admin_homework_list',
                        '/api/admin_create_homework',
                        '/api/admin_delete_homework',
                        '/api/available_students'
                    ]
                }
            })
            
        except Exception as e:
            traceback.print_exc()
            return self.error(f"Debug error: {str(e)}")