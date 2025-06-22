from django.db import transaction
from django.db.models import Q, Count, Avg
from django.utils import timezone
from rest_framework import status

from account.decorators import super_admin_required, admin_role_required
from account.models import User
from problem.models import Problem
from submission.models import Submission, JudgeStatus
from utils.api import APIView, validate_serializer

from ..models import (
    AdminStudentRelation, HomeworkAssignment, HomeworkProblem,
    StudentHomework, HomeworkSubmission
)
from ..serializers import (
    AdminStudentRelationSerializer, AssignStudentsSerializer,
    CreateHomeworkSerializer, HomeworkAssignmentSerializer,
    HomeworkDetailSerializer, StudentHomeworkSerializer,
    GradeHomeworkSerializer
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


class AdminListAPI(APIView):
    """Get list of admins (for superadmin)"""
    
    @super_admin_required
    def get(self, request):
        """Get all admin users"""
        admins = User.objects.filter(
            admin_type__in=['Admin', 'Super Admin']
        ).order_by('username')
        
        admin_data = []
        for admin in admins:
            student_count = AdminStudentRelation.objects.filter(
                admin=admin, is_active=True
            ).count()
            
            admin_data.append({
                'id': admin.id,
                'username': admin.username,
                'email': admin.email,
                'admin_type': admin.admin_type,
                'student_count': student_count
            })
        
        return self.success(admin_data)


class HomeworkManagementAPI(APIView):
    """Admin endpoint to manage homework assignments"""
    
    @admin_role_required
    def get(self, request):
        """Get homework assignments created by admin"""
        # Get homework created by this admin
        homework = HomeworkAssignment.objects.filter(
            created_by=request.user
        ).annotate(
            problems_count=Count('problems'),
            students_count=Count('assigned_students')
        ).order_by('-created_at')
        
        return self.success(self.paginate_data(
            request, homework, HomeworkAssignmentSerializer
        ))
    
    @admin_role_required
    @validate_serializer(CreateHomeworkSerializer)
    def post(self, request):
        """Create a new homework assignment"""
        data = request.data
        
        with transaction.atomic():
            # Create homework assignment
            homework = HomeworkAssignment.objects.create(
                title=data['title'],
                description=data['description'],
                created_by=request.user,
                due_date=data['due_date'],
                allow_late_submission=data.get('allow_late_submission', False),
                late_penalty_percent=data.get('late_penalty_percent', 0),
                max_attempts=data.get('max_attempts', 0)
            )
            
            # Add problems to homework
            for idx, problem_data in enumerate(data['problems']):
                HomeworkProblem.objects.create(
                    homework=homework,
                    problem_id=problem_data['problem_id'],
                    order=problem_data.get('order', idx),
                    points=problem_data.get('points', 100),
                    required=problem_data.get('required', True)
                )
            
            # Assign to students if specified
            if 'student_ids' in data:
                # Get students managed by this admin
                managed_students = AdminStudentRelation.objects.filter(
                    admin=request.user,
                    is_active=True,
                    student_id__in=data['student_ids']
                ).values_list('student_id', flat=True)
                
                for student_id in managed_students:
                    StudentHomework.objects.create(
                        student_id=student_id,
                        homework=homework
                    )
        
        return self.success({
            'homework': HomeworkDetailSerializer(homework).data,
            'message': 'Homework created successfully'
        })
    
    @admin_role_required
    def put(self, request):
        """Update homework assignment"""
        homework_id = request.data.get('id')
        if not homework_id:
            return self.error("Homework ID is required")
        
        try:
            homework = HomeworkAssignment.objects.get(
                id=homework_id,
                created_by=request.user
            )
        except HomeworkAssignment.DoesNotExist:
            return self.error("Homework not found or you don't have permission")
        
        # Update allowed fields
        allowed_fields = ['title', 'description', 'due_date', 'is_active',
                         'allow_late_submission', 'late_penalty_percent', 'max_attempts']
        
        for field in allowed_fields:
            if field in request.data:
                setattr(homework, field, request.data[field])
        
        homework.save()
        
        return self.success({
            'homework': HomeworkDetailSerializer(homework).data,
            'message': 'Homework updated successfully'
        })


class HomeworkDetailAPI(APIView):
    """Get detailed homework information"""
    
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
        
        # Get student progress
        student_homework = StudentHomework.objects.filter(
            homework=homework
        ).select_related('student').order_by('student__username')
        
        student_progress = []
        for sh in student_homework:
            progress = sh.calculate_progress()
            submissions = HomeworkSubmission.objects.filter(
                student_homework=sh
            ).select_related('problem')
            
            student_progress.append({
                'student_id': sh.student.id,
                'student_username': sh.student.username,
                'status': sh.status,
                'progress': progress,
                'submitted_at': sh.submitted_at,
                'total_score': sh.total_score,
                'grade_percent': sh.grade_percent,
                'problems_completed': submissions.filter(is_accepted=True).count(),
                'total_attempts': submissions.aggregate(total=Count('id'))['total'] or 0
            })
        
        return self.success({
            'homework': HomeworkDetailSerializer(homework).data,
            'student_progress': student_progress
        })


class AssignHomeworkToStudentsAPI(APIView):
    """Assign existing homework to more students"""
    
    @admin_role_required
    def post(self, request):
        """Assign homework to students"""
        homework_id = request.data.get('homework_id')
        student_ids = request.data.get('student_ids', [])
        
        if not homework_id or not student_ids:
            return self.error("Homework ID and student IDs are required")
        
        try:
            homework = HomeworkAssignment.objects.get(
                id=homework_id,
                created_by=request.user
            )
        except HomeworkAssignment.DoesNotExist:
            return self.error("Homework not found or you don't have permission")
        
        # Get students managed by this admin
        managed_students = AdminStudentRelation.objects.filter(
            admin=request.user,
            is_active=True,
            student_id__in=student_ids
        ).values_list('student_id', flat=True)
        
        assigned = []
        already_assigned = []
        
        with transaction.atomic():
            for student_id in managed_students:
                sh, created = StudentHomework.objects.get_or_create(
                    student_id=student_id,
                    homework=homework
                )
                
                if created:
                    assigned.append(student_id)
                else:
                    already_assigned.append(student_id)
        
        return self.success({
            'assigned': assigned,
            'already_assigned': already_assigned,
            'message': f'Successfully assigned homework to {len(assigned)} students'
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
        ).aggregate(total=Avg('points'))['total'] or 0
        
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
            'student_homework': StudentHomeworkSerializer(student_homework).data,
            'message': 'Homework graded successfully'
        })


class StudentListAPI(APIView):
    """Get list of students managed by admin"""
    
    @admin_role_required
    def get(self, request):
        """Get students managed by this admin"""
        # Get all students managed by this admin
        student_ids = AdminStudentRelation.objects.filter(
            admin=request.user,
            is_active=True
        ).values_list('student_id', flat=True)
        
        students = User.objects.filter(id__in=student_ids).order_by('username')
        
        student_data = []
        for student in students:
            # Get homework statistics
            homework_stats = StudentHomework.objects.filter(
                student=student
            ).aggregate(
                total=Count('id'),
                completed=Count('id', filter=Q(status='graded')),
                avg_grade=Avg('grade_percent')
            )
            
            student_data.append({
                'id': student.id,
                'username': student.username,
                'email': student.email,
                'total_homework': homework_stats['total'] or 0,
                'completed_homework': homework_stats['completed'] or 0,
                'avg_grade': homework_stats['avg_grade'] or 0
            })
        
        return self.success(student_data)