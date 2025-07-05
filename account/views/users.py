from django.db.models import Q, Count
from utils.api.api import APIView
from account.decorators import login_required, admin_role_required
from account.models import User, AdminType
from account.serializers import UserSerializer
from homework.models import AdminStudentRelation


class UsersAPI(APIView):
    """GET /api/users - Alternative endpoint for getting users/students"""
    
    @admin_role_required
    def get(self, request):
        """Get users based on filters"""
        # Get query parameters
        user_type = request.GET.get('type', 'student')  # 'student', 'admin', 'all'
        search = request.GET.get('search', '')
        group = request.GET.get('group', '')
        
        # Base queryset
        users = User.objects.select_related('userprofile')
        
        # Filter by user type
        if user_type == 'student':
            users = users.filter(admin_type=AdminType.REGULAR_USER)
        elif user_type == 'admin':
            users = users.filter(admin_type__in=[AdminType.ADMIN, AdminType.SUPER_ADMIN])
        # else 'all' - no filter
        
        # Search filter
        if search:
            users = users.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(userprofile__real_name__icontains=search)
            )
        
        # Group filter
        if group:
            users = users.filter(userprofile__student_group=group)
        
        # For regular admins, only show their managed students
        if request.user.admin_type != AdminType.SUPER_ADMIN and user_type == 'student':
            managed_student_ids = AdminStudentRelation.objects.filter(
                admin=request.user,
                is_active=True
            ).values_list('student_id', flat=True)
            users = users.filter(id__in=managed_student_ids)
        
        # Order by username
        users = users.order_by('username')
        
        # Serialize data
        user_data = []
        for user in users:
            data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'real_name': user.userprofile.real_name if hasattr(user, 'userprofile') else '',
                'admin_type': user.admin_type,
                'is_disabled': user.is_disabled,
                'create_time': user.create_time.isoformat() if user.create_time else None
            }
            
            # Add student-specific fields
            if hasattr(user, 'userprofile'):
                data.update({
                    'school': user.userprofile.school,
                    'major': user.userprofile.major,
                    'student_group': user.userprofile.student_group,
                    'accepted_number': user.userprofile.accepted_number,
                    'submission_number': user.userprofile.submission_number
                })
            
            user_data.append(data)
        
        # Add pagination if needed
        page = request.GET.get('page')
        if page:
            return self.success(self.paginate_data(request, users, UserSerializer))
        else:
            return self.success(user_data)


class StudentsByGroupAPI(APIView):
    """GET /api/students_by_group - Get students organized by group/class"""
    
    @admin_role_required
    def get(self, request):
        """Get students organized by their groups"""
        # Get all students
        if request.user.admin_type == AdminType.SUPER_ADMIN:
            students = User.objects.filter(
                admin_type=AdminType.REGULAR_USER
            ).select_related('userprofile')
        else:
            # Regular admin - only their managed students
            managed_student_ids = AdminStudentRelation.objects.filter(
                admin=request.user,
                is_active=True
            ).values_list('student_id', flat=True)
            students = User.objects.filter(
                id__in=managed_student_ids
            ).select_related('userprofile')
        
        # Group students by their group/class
        groups = {}
        ungrouped = []
        
        for student in students:
            student_data = {
                'id': student.id,
                'username': student.username,
                'email': student.email,
                'real_name': student.userprofile.real_name if hasattr(student, 'userprofile') else '',
                'student_group': student.userprofile.student_group if hasattr(student, 'userprofile') else None
            }
            
            if hasattr(student, 'userprofile') and student.userprofile.student_group:
                group_name = student.userprofile.student_group
                if group_name not in groups:
                    groups[group_name] = {
                        'name': group_name,
                        'students': []
                    }
                groups[group_name]['students'].append(student_data)
            else:
                ungrouped.append(student_data)
        
        # Convert groups dict to list
        groups_list = list(groups.values())
        
        # Sort groups by name
        groups_list.sort(key=lambda x: x['name'])
        
        # Add ungrouped students as a special group if any exist
        if ungrouped:
            groups_list.append({
                'name': 'Ungrouped',
                'students': ungrouped
            })
        
        # Add summary statistics
        total_students = sum(len(g['students']) for g in groups_list)
        
        return self.success({
            'groups': groups_list,
            'total_groups': len(groups_list) - (1 if ungrouped else 0),
            'total_students': total_students,
            'ungrouped_count': len(ungrouped)
        })


class UpdateStudentGroupAPI(APIView):
    """POST /api/update_student_group - Update student's group/class"""
    
    @admin_role_required
    def post(self, request):
        """Update a student's group"""
        student_id = request.data.get('student_id')
        group_name = request.data.get('group_name', '').strip()
        
        if not student_id:
            return self.error("Student ID is required")
        
        # Check if admin has permission to manage this student
        if request.user.admin_type != AdminType.SUPER_ADMIN:
            if not AdminStudentRelation.objects.filter(
                admin=request.user,
                student_id=student_id,
                is_active=True
            ).exists():
                return self.error("You don't have permission to manage this student")
        
        try:
            user = User.objects.get(id=student_id, admin_type=AdminType.REGULAR_USER)
            
            # Update or create user profile
            from account.models import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.student_group = group_name if group_name else None
            profile.save()
            
            return self.success({
                'message': 'Student group updated successfully',
                'student_id': student_id,
                'group_name': group_name or 'Ungrouped'
            })
            
        except User.DoesNotExist:
            return self.error("Student not found")


class AvailableGroupsAPI(APIView):
    """GET /api/available_groups - Get list of available student groups"""
    
    @admin_role_required
    def get(self, request):
        """Get all unique student groups"""
        # Get distinct group names
        groups = User.objects.filter(
            admin_type=AdminType.REGULAR_USER,
            userprofile__student_group__isnull=False
        ).values_list('userprofile__student_group', flat=True).distinct()
        
        # Filter out empty strings
        groups = [g for g in groups if g and g.strip()]
        
        # Sort alphabetically
        groups.sort()
        
        return self.success({
            'groups': groups,
            'count': len(groups)
        })


class StudentsByGroupNameAPI(APIView):
    """GET /api/students/group/{name} - Get students in a specific group"""
    
    @admin_role_required
    def get(self, request, group_name):
        """Get all students in a specific group"""
        # Base query for students in this group
        students = User.objects.filter(
            admin_type=AdminType.REGULAR_USER,
            userprofile__student_group=group_name
        ).select_related('userprofile')
        
        # For regular admins, only show their managed students
        if request.user.admin_type != AdminType.SUPER_ADMIN:
            managed_student_ids = AdminStudentRelation.objects.filter(
                admin=request.user,
                is_active=True
            ).values_list('student_id', flat=True)
            students = students.filter(id__in=managed_student_ids)
        
        # Order by username
        students = students.order_by('username')
        
        # Build response data
        student_data = []
        for student in students:
            data = {
                'id': student.id,
                'username': student.username,
                'email': student.email,
                'real_name': student.userprofile.real_name if hasattr(student, 'userprofile') else '',
                'student_group': group_name,
                'school': student.userprofile.school if hasattr(student, 'userprofile') else '',
                'major': student.userprofile.major if hasattr(student, 'userprofile') else '',
                'accepted_number': student.userprofile.accepted_number if hasattr(student, 'userprofile') else 0,
                'submission_number': student.userprofile.submission_number if hasattr(student, 'userprofile') else 0
            }
            student_data.append(data)
        
        return self.success({
            'group_name': group_name,
            'students': student_data,
            'count': len(student_data)
        })