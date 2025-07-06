from rest_framework import serializers
from django.utils import timezone
from django.db import models
from account.models import User
from account.serializers import UserSerializer
from problem.models import Problem
from problem.serializers import ProblemSerializer
from .models import (
    AdminStudentRelation, HomeworkAssignment, HomeworkProblem,
    StudentHomework, HomeworkSubmission, HomeworkComment
)


class AdminStudentRelationSerializer(serializers.ModelSerializer):
    admin_username = serializers.CharField(source='admin.username', read_only=True)
    student_username = serializers.CharField(source='student.username', read_only=True)
    assigned_by_username = serializers.CharField(source='assigned_by.username', read_only=True)
    
    class Meta:
        model = AdminStudentRelation
        fields = ['id', 'admin', 'admin_username', 'student', 'student_username', 
                  'assigned_by', 'assigned_by_username', 'assigned_at', 'is_active']


class AssignStudentsSerializer(serializers.Serializer):
    admin_id = serializers.IntegerField()
    student_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    
    def validate_admin_id(self, value):
        try:
            admin = User.objects.get(id=value)
            if not admin.is_admin_role():
                raise serializers.ValidationError("User is not an admin")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Admin user not found")
    
    def validate_student_ids(self, value):
        students = User.objects.filter(id__in=value)
        if students.count() != len(value):
            raise serializers.ValidationError("Some student IDs are invalid")
        
        # Check if any of the users are admins
        admin_users = [s for s in students if s.is_admin_role()]
        if admin_users:
            raise serializers.ValidationError(f"Users {[u.username for u in admin_users]} are admins, not students")
        
        return value


class HomeworkProblemSerializer(serializers.ModelSerializer):
    problem_title = serializers.CharField(source='problem.title', read_only=True)
    problem_difficulty = serializers.CharField(source='problem.difficulty', read_only=True)
    problem_id = serializers.IntegerField(source='problem.id', read_only=True)
    problem_display_id = serializers.CharField(source='problem._id', read_only=True)
    
    class Meta:
        model = HomeworkProblem
        fields = ['id', 'problem', 'problem_id', 'problem_display_id', 'problem_title', 
                  'problem_difficulty', 'order', 'points', 'required']


class CreateHomeworkSerializer(serializers.ModelSerializer):
    problem_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )
    student_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = HomeworkAssignment
        fields = ['title', 'description', 'due_date', 'problem_ids', 'student_ids',
                  'allow_late_submission', 'late_penalty_percent', 'max_attempts', 'auto_grade']
    
    def validate_due_date(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Due date must be in the future")
        return value
    
    def validate_problem_ids(self, value):
        if not value:
            raise serializers.ValidationError("At least one problem is required")
            
        # Check if all problems exist
        existing_problems = Problem.objects.filter(id__in=value).count()
        if existing_problems != len(value):
            raise serializers.ValidationError("Some problem IDs are invalid")
            
        return value


class HomeworkAssignmentSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    problems_count = serializers.IntegerField(source='problems.count', read_only=True)
    assigned_students_count = serializers.IntegerField(source='assigned_students.count', read_only=True)
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = HomeworkAssignment
        fields = ['id', 'title', 'description', 'created_by', 'created_by_username',
                  'created_at', 'updated_at', 'due_date', 'is_active', 'is_overdue',
                  'problems_count', 'assigned_students_count', 'allow_late_submission',
                  'late_penalty_percent', 'max_attempts']
    
    def get_is_overdue(self, obj):
        return obj.is_overdue()


class HomeworkDetailSerializer(HomeworkAssignmentSerializer):
    problems = HomeworkProblemSerializer(source='homeworkproblem_set', many=True, read_only=True)
    
    class Meta(HomeworkAssignmentSerializer.Meta):
        fields = HomeworkAssignmentSerializer.Meta.fields + ['problems']


class StudentHomeworkSerializer(serializers.ModelSerializer):
    homework_title = serializers.CharField(source='homework.title', read_only=True)
    student_username = serializers.CharField(source='student.username', read_only=True)
    progress = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentHomework
        fields = ['id', 'student', 'student_username', 'homework', 'homework_title',
                  'assigned_at', 'status', 'started_at', 'submitted_at', 'progress',
                  'total_score', 'max_possible_score', 'grade_percent', 'is_overdue',
                  'graded_at', 'feedback']
    
    def get_progress(self, obj):
        return obj.calculate_progress()
    
    def get_is_overdue(self, obj):
        return obj.homework.is_overdue()


class StudentHomeworkDetailSerializer(StudentHomeworkSerializer):
    homework = HomeworkDetailSerializer(read_only=True)
    submissions = serializers.SerializerMethodField()
    
    class Meta(StudentHomeworkSerializer.Meta):
        fields = StudentHomeworkSerializer.Meta.fields + ['homework', 'submissions']
    
    def get_submissions(self, obj):
        submissions = HomeworkSubmission.objects.filter(
            student_homework=obj
        ).select_related('problem')
        return HomeworkSubmissionSerializer(submissions, many=True).data


class HomeworkSubmissionSerializer(serializers.ModelSerializer):
    problem_title = serializers.CharField(source='problem.title', read_only=True)
    
    class Meta:
        model = HomeworkSubmission
        fields = ['id', 'problem', 'problem_title', 'submission_id', 
                  'submitted_at', 'is_accepted', 'score', 'attempts']


class SubmitHomeworkSerializer(serializers.Serializer):
    homework_id = serializers.IntegerField()
    problem_id = serializers.IntegerField()
    submission_id = serializers.CharField()
    
    def validate(self, data):
        # Validate homework exists and is assigned to user
        try:
            homework = HomeworkAssignment.objects.get(id=data['homework_id'])
        except HomeworkAssignment.DoesNotExist:
            raise serializers.ValidationError("Homework not found")
        
        # Check if problem is in homework
        if not homework.problems.filter(id=data['problem_id']).exists():
            raise serializers.ValidationError("Problem not in this homework")
        
        return data


class GradeHomeworkSerializer(serializers.Serializer):
    student_homework_id = serializers.IntegerField()
    total_score = serializers.FloatField(min_value=0)
    feedback = serializers.CharField(required=False, allow_blank=True)
    
    def validate_student_homework_id(self, value):
        try:
            StudentHomework.objects.get(id=value)
            return value
        except StudentHomework.DoesNotExist:
            raise serializers.ValidationError("Student homework not found")


class HomeworkCommentSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.username', read_only=True)
    author_id = serializers.IntegerField(source='author.id', read_only=True)
    can_delete = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    is_pinned = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = HomeworkComment
        fields = ['id', 'author', 'author_id', 'content', 'created_at', 'updated_at', 
                  'is_pinned', 'can_delete', 'replies', 'parent']
    
    def get_can_delete(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        # User can delete their own comments or if they're an admin
        return obj.author == request.user or request.user.is_admin_role()
    
    def get_replies(self, obj):
        # Only get replies for top-level comments
        if obj.parent:
            return []
        replies = obj.replies.all().order_by('created_at')
        return HomeworkCommentSerializer(replies, many=True, context=self.context).data


class CreateHomeworkCommentSerializer(serializers.Serializer):
    homework_id = serializers.IntegerField(required=True)
    content = serializers.CharField(required=True, min_length=1, max_length=5000)
    parent_id = serializers.IntegerField(required=False, allow_null=True)
    is_pinned = serializers.BooleanField(required=False, default=False)


# API Response Serializers for frontend compatibility
class ProblemStatusSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='id')  # HomeworkProblem ID
    problem_id = serializers.IntegerField(source='problem.id')
    _id = serializers.CharField(source='problem._id')
    title = serializers.CharField(source='problem.title')
    difficulty = serializers.CharField(source='problem.difficulty')
    score = serializers.IntegerField(source='points')
    status = serializers.SerializerMethodField()
    attempts = serializers.SerializerMethodField()
    order = serializers.IntegerField()
    
    def get_status(self, obj):
        # Get submission status for this student
        student_homework = self.context.get('student_homework')
        if not student_homework:
            return 'not_started'
            
        submission = HomeworkSubmission.objects.filter(
            student_homework=student_homework,
            problem=obj.problem
        ).first()
        
        if not submission:
            return 'not_started'
        elif submission.is_accepted:
            return 'solved'
        else:
            return 'attempted'
    
    def get_attempts(self, obj):
        student_homework = self.context.get('student_homework')
        if not student_homework:
            return 0
            
        submission = HomeworkSubmission.objects.filter(
            student_homework=student_homework,
            problem=obj.problem
        ).first()
        
        return submission.attempts if submission else 0


class StudentHomeworkListSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='homework.title')
    description = serializers.CharField(source='homework.description')
    due_date = serializers.DateTimeField(source='homework.due_date')
    assigned_by = serializers.SerializerMethodField()
    problem_count = serializers.IntegerField(source='homework.problems.count')
    progress = serializers.SerializerMethodField()
    grade = serializers.FloatField(source='grade_percent', allow_null=True)
    
    class Meta:
        model = StudentHomework
        fields = ['id', 'title', 'description', 'due_date', 'assigned_by', 
                  'status', 'problem_count', 'progress', 'grade']
    
    def get_assigned_by(self, obj):
        return obj.homework.created_by.username
    
    def get_progress(self, obj):
        return obj.calculate_progress()


class StudentHomeworkDetailSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()  # StudentHomework ID
    title = serializers.CharField(source='homework.title')
    description = serializers.CharField(source='homework.description')
    due_date = serializers.DateTimeField(source='homework.due_date')
    status = serializers.CharField()
    problems = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(source='homework.created_at')
    max_attempts = serializers.SerializerMethodField()
    late_penalty_percent = serializers.IntegerField(source='homework.late_penalty_percent')
    feedback = serializers.CharField(allow_null=True, allow_blank=True)
    total_score = serializers.SerializerMethodField()
    earned_score = serializers.FloatField(source='total_score', allow_null=True)
    
    class Meta:
        model = StudentHomework
        fields = ['id', 'title', 'description', 'due_date', 'status', 'problems',
                  'created_at', 'max_attempts', 'late_penalty_percent', 'feedback',
                  'total_score', 'earned_score']
    
    def get_problems(self, obj):
        homework_problems = HomeworkProblem.objects.filter(
            homework=obj.homework
        ).select_related('problem').order_by('order')
        
        problem_data = []
        for hp in homework_problems:
            serializer = ProblemStatusSerializer(
                hp,
                context={'student_homework': obj}
            )
            problem_data.append(serializer.data)
        
        return problem_data
    
    def get_total_score(self, obj):
        # Calculate total possible score from all problems
        return HomeworkProblem.objects.filter(
            homework=obj.homework
        ).aggregate(total=models.Sum('points'))['total'] or 0
    
    def get_max_attempts(self, obj):
        # Return None if 0 (unlimited), otherwise return the value
        return None if obj.homework.max_attempts == 0 else obj.homework.max_attempts


class AdminHomeworkListSerializer(serializers.ModelSerializer):
    problems = serializers.SerializerMethodField()
    assigned_students = serializers.SerializerMethodField()
    
    class Meta:
        model = HomeworkAssignment
        fields = ['id', 'title', 'description', 'due_date', 'created_at',
                  'is_active', 'problems', 'assigned_students']
    
    def get_problems(self, obj):
        homework_problems = HomeworkProblem.objects.filter(
            homework=obj
        ).select_related('problem').order_by('order')
        
        return [{
            'id': hp.problem.id,
            '_id': hp.problem._id,
            'title': hp.problem.title
        } for hp in homework_problems]
    
    def get_assigned_students(self, obj):
        student_homework = StudentHomework.objects.filter(
            homework=obj
        ).select_related('student')
        
        return [{
            'id': sh.student.id,
            'username': sh.student.username,
            'email': sh.student.email
        } for sh in student_homework]


class AvailableStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']