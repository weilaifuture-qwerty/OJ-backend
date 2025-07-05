from django.db import transaction
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from rest_framework import status

from account.decorators import super_admin_required, admin_role_required
from account.models import User, AdminType
from problem.models import Problem
from submission.models import Submission, JudgeStatus
from utils.api.api import APIView, validate_serializer

from ..models import (
    AdminStudentRelation, HomeworkAssignment, HomeworkProblem,
    StudentHomework, HomeworkSubmission
)
from ..serializers import (
    AdminStudentRelationSerializer, AssignStudentsSerializer,
    CreateHomeworkSerializer, HomeworkAssignmentSerializer,
    AdminHomeworkListSerializer, StudentHomeworkSerializer,
    GradeHomeworkSerializer, AvailableStudentSerializer
)


class AdminStudentManagementAPI(APIView):
    """Superadmin endpoint to manage admin-student relationships"""
    
    @super_admin_required
    def get(self, request):
        """Get all admin-student relationships"""
        admin_id = request.GET.get('admin_id')
        student_id = request.GET.get('student_id')
        
        relations = AdminStudentRelation.objects.filter(is_active=True)
        
        if admin_id:
            relations = relations.filter(admin_id=admin_id)
        if student_id:
            relations = relations.filter(student_id=student_id)
            
        relations = relations.select_related('admin', 'student', 'assigned_by')
        
        return self.success(self.paginate_data(
            request, relations, AdminStudentRelationSerializer
        ))
    
    @super_admin_required
    @validate_serializer(AssignStudentsSerializer)
    def post(self, request):
        """Assign students to an admin"""
        data = request.data
        admin_id = data['admin_id']
        student_ids = data['student_ids']
        
        created_relations = []
        already_assigned = []
        
        with transaction.atomic():
            for student_id in student_ids:
                relation, created = AdminStudentRelation.objects.get_or_create(
                    admin_id=admin_id,
                    student_id=student_id,
                    defaults={
                        'assigned_by': request.user,
                        'is_active': True
                    }
                )
                
                if created:
                    created_relations.append(relation)
                else:
                    if not relation.is_active:
                        relation.is_active = True
                        relation.assigned_by = request.user
                        relation.save()
                        created_relations.append(relation)
                    else:
                        already_assigned.append(student_id)
        
        return self.success({
            'created': AdminStudentRelationSerializer(created_relations, many=True).data,
            'already_assigned': already_assigned,
            'message': f'Successfully assigned {len(created_relations)} students'
        })
    
    @super_admin_required
    def delete(self, request):
        """Remove admin-student relationship"""
        relation_id = request.GET.get('id')
        if not relation_id:
            return self.error("Relation ID is required")
        
        try:
            relation = AdminStudentRelation.objects.get(id=relation_id)
            relation.is_active = False
            relation.save()
            return self.success("Relationship removed successfully")
        except AdminStudentRelation.DoesNotExist:
            return self.error("Relationship not found")


class AdminHomeworkListAPI(APIView):
    """GET /api/admin_homework_list - Get admin's homework list"""
    
    @admin_role_required
    def get(self, request):
        """Get homework assignments created by admin"""
        try:
            # Get homework created by this admin (only active ones)
            homework = HomeworkAssignment.objects.filter(
                created_by=request.user,
                is_active=True
            ).prefetch_related(
                'homeworkproblem_set__problem',
                'studenthomework_set__student'
            ).order_by('-created_at')
            
            # Use the AdminHomeworkListSerializer for proper response format
            serialized_data = self.paginate_data(request, homework, AdminHomeworkListSerializer)
            
            return self.success(serialized_data)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return self.server_error()


class AdminCreateHomeworkAPI(APIView):
    """POST /api/admin_create_homework - Create new homework"""
    
    @admin_role_required
    @validate_serializer(CreateHomeworkSerializer)
    def post(self, request):
        """Create a new homework assignment"""
        try:
            # The data is already validated by the decorator
            serializer = request.serializer
            validated_data = serializer.validated_data
            
            with transaction.atomic():
                # Create homework assignment
                homework_data = {
                    'title': validated_data['title'],
                    'description': validated_data['description'],
                    'created_by': request.user,
                    'due_date': validated_data['due_date'],
                    'allow_late_submission': validated_data.get('allow_late_submission', False),
                    'late_penalty_percent': validated_data.get('late_penalty_percent', 0),
                    'max_attempts': validated_data.get('max_attempts', 0)
                }
                
                # Only add auto_grade if the field exists in the model
                try:
                    HomeworkAssignment._meta.get_field('auto_grade')
                    homework_data['auto_grade'] = validated_data.get('auto_grade', True)
                except:
                    pass
                
                homework = HomeworkAssignment.objects.create(**homework_data)
                
                # Add problems to homework
                problem_ids = validated_data.get('problem_ids', [])
                
                for idx, problem_id in enumerate(problem_ids):
                    HomeworkProblem.objects.create(
                        homework=homework,
                        problem_id=problem_id,
                        order=idx,
                        points=100,  # Default points
                        required=True
                    )
                
                # Assign to students
                student_ids = validated_data.get('student_ids', [])
                
                if request.user.admin_type == AdminType.SUPER_ADMIN:
                    # Super admin can assign to any students
                    if student_ids:
                        # Assign to specific students
                        for student_id in student_ids:
                            # Verify student exists and is a regular user
                            if User.objects.filter(id=student_id, admin_type=AdminType.REGULAR_USER).exists():
                                StudentHomework.objects.create(
                                    student_id=student_id,
                                    homework=homework
                                )
                    else:
                        # Assign to all students
                        all_students = User.objects.filter(admin_type=AdminType.REGULAR_USER)
                        for student in all_students:
                            StudentHomework.objects.create(
                                student=student,
                                homework=homework
                            )
                else:
                    # Regular admin can only assign to their managed students
                    if student_ids:
                        # Assign to specific students managed by this admin
                        managed_students = AdminStudentRelation.objects.filter(
                            admin=request.user,
                            is_active=True,
                            student_id__in=student_ids
                        ).values_list('student_id', flat=True)
                        
                        for student_id in managed_students:
                            StudentHomework.objects.create(
                                student_id=student_id,
                                homework=homework
                            )
                    else:
                        # Assign to all students managed by this admin
                        all_managed_students = AdminStudentRelation.objects.filter(
                            admin=request.user,
                            is_active=True
                        ).values_list('student_id', flat=True)
                        
                        for student_id in all_managed_students:
                            StudentHomework.objects.create(
                                student_id=student_id,
                                homework=homework
                            )
            
            return self.success({
                'id': homework.id,
                'message': 'Homework created successfully'
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return self.server_error()


class AdminUpdateHomeworkAPI(APIView):
    """PUT /api/admin/homework/<id> - Update homework"""
    
    @admin_role_required
    def put(self, request, homework_id):
        """Update an existing homework assignment"""
        try:
            # Get the homework assignment
            homework = HomeworkAssignment.objects.get(
                id=homework_id,
                created_by=request.user,
                is_active=True
            )
        except HomeworkAssignment.DoesNotExist:
            return self.error("Homework not found or you don't have permission")
        
        # Update fields if provided
        if 'title' in request.data:
            homework.title = request.data['title']
        
        if 'description' in request.data:
            homework.description = request.data['description']
        
        if 'due_date' in request.data:
            homework.due_date = request.data['due_date']
        
        if 'allow_late_submission' in request.data:
            homework.allow_late_submission = request.data['allow_late_submission']
        
        if 'late_penalty_percent' in request.data:
            homework.late_penalty_percent = request.data['late_penalty_percent']
        
        if 'max_attempts' in request.data:
            homework.max_attempts = request.data['max_attempts']
        
        # Update auto_grade if the field exists
        if 'auto_grade' in request.data:
            try:
                HomeworkAssignment._meta.get_field('auto_grade')
                homework.auto_grade = request.data['auto_grade']
            except:
                pass
        
        # Save the changes
        homework.save()
        
        # Update problems if provided
        if 'problem_ids' in request.data:
            with transaction.atomic():
                # Remove existing problems
                HomeworkProblem.objects.filter(homework=homework).delete()
                
                # Add new problems
                problem_ids = request.data['problem_ids']
                for idx, problem_id in enumerate(problem_ids):
                    HomeworkProblem.objects.create(
                        homework=homework,
                        problem_id=problem_id,
                        order=idx,
                        points=100,  # Default points
                        required=True
                    )
        
        # Update student assignments if provided
        if 'student_ids' in request.data:
            with transaction.atomic():
                # Get current student IDs
                current_student_ids = set(StudentHomework.objects.filter(
                    homework=homework
                ).values_list('student_id', flat=True))
                
                new_student_ids = set(request.data['student_ids'])
                
                # Remove students that are no longer assigned
                students_to_remove = current_student_ids - new_student_ids
                StudentHomework.objects.filter(
                    homework=homework,
                    student_id__in=students_to_remove
                ).delete()
                
                # Add new students
                students_to_add = new_student_ids - current_student_ids
                
                if request.user.admin_type == AdminType.SUPER_ADMIN:
                    # Super admin can assign to any students
                    for student_id in students_to_add:
                        if User.objects.filter(id=student_id, admin_type=AdminType.REGULAR_USER).exists():
                            StudentHomework.objects.create(
                                student_id=student_id,
                                homework=homework
                            )
                else:
                    # Regular admin can only assign to their managed students
                    managed_students = AdminStudentRelation.objects.filter(
                        admin=request.user,
                        is_active=True,
                        student_id__in=students_to_add
                    ).values_list('student_id', flat=True)
                    
                    for student_id in managed_students:
                        StudentHomework.objects.create(
                            student_id=student_id,
                            homework=homework
                        )
        
        return self.success({
            'id': homework.id,
            'message': 'Homework updated successfully'
        })


class AdminDeleteHomeworkAPI(APIView):
    """DELETE /api/admin_delete_homework - Delete homework"""
    
    @admin_role_required
    def delete(self, request):
        """Delete a homework assignment"""
        homework_id = request.GET.get('id')
        if not homework_id:
            return self.error("Homework ID is required")
        
        try:
            homework = HomeworkAssignment.objects.get(
                id=homework_id,
                created_by=request.user
            )
            
            # Soft delete by marking as inactive
            homework.is_active = False
            homework.save()
            
            return self.success({'message': 'Homework deleted successfully'})
            
        except HomeworkAssignment.DoesNotExist:
            return self.error("Homework not found or you don't have permission")


class AvailableStudentsAPI(APIView):
    """GET /api/available_students - Get students available for assignment"""
    
    @admin_role_required
    def get(self, request):
        """Get students managed by this admin with enhanced information"""
        # Get query parameters
        search = request.GET.get('search', '')
        group = request.GET.get('group', '')
        exclude_homework_id = request.GET.get('exclude_homework_id')
        
        # Base query for students
        if request.user.admin_type == AdminType.SUPER_ADMIN:
            students = User.objects.filter(
                admin_type=AdminType.REGULAR_USER
            ).select_related('userprofile')
        else:
            # Regular admin can only see their managed students
            student_ids = AdminStudentRelation.objects.filter(
                admin=request.user,
                is_active=True
            ).values_list('student_id', flat=True)
            
            students = User.objects.filter(
                id__in=student_ids
            ).select_related('userprofile')
        
        # Apply search filter
        if search:
            students = students.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(userprofile__real_name__icontains=search)
            )
        
        # Apply group filter
        if group:
            students = students.filter(userprofile__student_group=group)
        
        # Exclude students already assigned to a specific homework
        if exclude_homework_id:
            assigned_student_ids = StudentHomework.objects.filter(
                homework_id=exclude_homework_id
            ).values_list('student_id', flat=True)
            students = students.exclude(id__in=assigned_student_ids)
        
        # Order by username
        students = students.order_by('username')
        
        # Build response data with additional fields
        student_data = []
        for student in students:
            data = {
                'id': student.id,
                'username': student.username,
                'email': student.email,
                'real_name': student.userprofile.real_name if hasattr(student, 'userprofile') else '',
                'student_group': student.userprofile.student_group if hasattr(student, 'userprofile') else None
            }
            
            # Add homework statistics
            homework_stats = StudentHomework.objects.filter(
                student=student
            ).aggregate(
                total_homework=Count('id'),
                completed_homework=Count('id', filter=Q(status='graded')),
                avg_grade=Avg('grade_percent', filter=Q(status='graded'))
            )
            
            data.update({
                'total_homework': homework_stats['total_homework'] or 0,
                'completed_homework': homework_stats['completed_homework'] or 0,
                'average_grade': round(homework_stats['avg_grade'] or 0, 2)
            })
            
            student_data.append(data)
        
        return self.success(student_data)


class AdminHomeworkDetailAPI(APIView):
    """Get detailed homework information with student progress"""
    
    @admin_role_required
    def get(self, request):
        """Get homework details with student progress"""
        homework_id = request.GET.get('id')
        if not homework_id:
            return self.error("Homework ID is required")
        
        try:
            homework = HomeworkAssignment.objects.get(
                id=homework_id,
                created_by=request.user
            )
        except HomeworkAssignment.DoesNotExist:
            return self.error("Homework not found or you don't have permission")
        
        # Get detailed homework data
        homework_data = AdminHomeworkListSerializer(homework).data
        
        # Get student progress
        student_homework = StudentHomework.objects.filter(
            homework=homework
        ).select_related('student').order_by('student__username')
        
        student_progress = []
        for sh in student_homework:
            progress = sh.calculate_progress()
            
            # Get submission stats
            submissions = HomeworkSubmission.objects.filter(
                student_homework=sh
            )
            
            problems_solved = submissions.filter(is_accepted=True).values('problem').distinct().count()
            total_attempts = submissions.aggregate(total=Sum('attempts'))['total'] or 0
            
            student_progress.append({
                'student_id': sh.student.id,
                'student_username': sh.student.username,
                'student_email': sh.student.email,
                'status': sh.status,
                'progress': progress,
                'problems_solved': problems_solved,
                'total_problems': homework.problems.count(),
                'total_attempts': total_attempts,
                'submitted_at': sh.submitted_at.isoformat() if sh.submitted_at else None,
                'total_score': sh.total_score,
                'grade_percent': sh.grade_percent,
                'graded_at': sh.graded_at.isoformat() if sh.graded_at else None
            })
        
        return self.success({
            'homework': homework_data,
            'student_progress': student_progress
        })


class GradeHomeworkAPI(APIView):
    """Grade student homework submissions"""
    
    @admin_role_required
    @validate_serializer(GradeHomeworkSerializer)
    def post(self, request):
        """Grade a student's homework"""
        data = request.data
        
        try:
            student_homework = StudentHomework.objects.get(
                id=data['student_homework_id'],
                homework__created_by=request.user
            )
        except StudentHomework.DoesNotExist:
            return self.error("Student homework not found or you don't have permission")
        
        # Calculate max possible score
        max_score = HomeworkProblem.objects.filter(
            homework=student_homework.homework
        ).aggregate(total=Sum('points'))['total'] or 100
        
        # Update grade
        student_homework.total_score = data['total_score']
        student_homework.max_possible_score = max_score
        student_homework.grade_percent = (data['total_score'] / max_score * 100) if max_score > 0 else 0
        student_homework.graded_at = timezone.now()
        student_homework.graded_by = request.user
        student_homework.feedback = data.get('feedback', '')
        student_homework.status = 'graded'
        student_homework.save()
        
        return self.success({
            'message': 'Homework graded successfully'
        })


class HomeworkStatisticsAPI(APIView):
    """Get homework statistics for admin dashboard"""
    
    @admin_role_required
    def get(self, request):
        """Get homework statistics"""
        # Get all homework created by this admin
        homework_ids = HomeworkAssignment.objects.filter(
            created_by=request.user,
            is_active=True
        ).values_list('id', flat=True)
        
        # Get statistics
        total_homework = len(homework_ids)
        
        student_homework = StudentHomework.objects.filter(
            homework_id__in=homework_ids
        )
        
        stats = {
            'total_homework': total_homework,
            'total_assignments': student_homework.count(),
            'status_breakdown': {
                'assigned': student_homework.filter(status='assigned').count(),
                'in_progress': student_homework.filter(status='in_progress').count(),
                'submitted': student_homework.filter(status='submitted').count(),
                'graded': student_homework.filter(status='graded').count(),
                'late': student_homework.filter(status='late').count()
            },
            'average_completion_rate': 0,
            'average_grade': 0
        }
        
        # Calculate average completion rate
        if student_homework.exists():
            completed = student_homework.filter(
                status__in=['submitted', 'graded']
            ).count()
            stats['average_completion_rate'] = round(
                (completed / student_homework.count()) * 100, 2
            )
        
        # Calculate average grade
        graded = student_homework.filter(
            status='graded',
            grade_percent__gt=0
        ).aggregate(avg_grade=Avg('grade_percent'))
        
        if graded['avg_grade']:
            stats['average_grade'] = round(graded['avg_grade'], 2)
        
        return self.success(stats)