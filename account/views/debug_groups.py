from utils.api import APIView
from account.models import User, UserProfile, AdminType
from django.db.models import Count

class DebugGroupsAPI(APIView):
    """Debug endpoint to check group data without authentication"""
    
    def get(self, request):
        """Get debug information about groups and students"""
        
        # Count students
        total_students = User.objects.filter(admin_type=AdminType.REGULAR_USER).count()
        
        # Count students with groups
        students_with_groups = UserProfile.objects.filter(
            user__admin_type=AdminType.REGULAR_USER,
            student_group__isnull=False
        ).exclude(student_group='').count()
        
        # Get group distribution
        group_distribution = UserProfile.objects.filter(
            user__admin_type=AdminType.REGULAR_USER
        ).exclude(
            student_group__isnull=True
        ).exclude(
            student_group=''
        ).values('student_group').annotate(
            count=Count('id')
        ).order_by('student_group')
        
        # Get sample students
        sample_students = []
        students = User.objects.filter(
            admin_type=AdminType.REGULAR_USER
        ).select_related('userprofile')[:5]
        
        for student in students:
            sample_students.append({
                'id': student.id,
                'username': student.username,
                'email': student.email,
                'admin_type': student.admin_type,
                'has_profile': hasattr(student, 'userprofile'),
                'student_group': student.userprofile.student_group if hasattr(student, 'userprofile') else None
            })
        
        # Get unique groups
        unique_groups = UserProfile.objects.filter(
            user__admin_type=AdminType.REGULAR_USER
        ).exclude(
            student_group__isnull=True
        ).exclude(
            student_group=''
        ).values_list('student_group', flat=True).distinct()
        
        return self.success({
            'total_students': total_students,
            'students_with_groups': students_with_groups,
            'students_without_groups': total_students - students_with_groups,
            'unique_groups': list(unique_groups),
            'group_distribution': list(group_distribution),
            'sample_students': sample_students,
            'debug_info': {
                'admin_types': {
                    'REGULAR_USER': AdminType.REGULAR_USER,
                    'ADMIN': AdminType.ADMIN,
                    'SUPER_ADMIN': AdminType.SUPER_ADMIN
                }
            }
        })