from rest_framework import serializers
from django.utils import timezone
from account.models import User
from problem.models import Problem
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
    
    class Meta:
        model = HomeworkProblem
        fields = ['id', 'problem', 'problem_title', 'problem_difficulty', 
                  'order', 'points', 'required']


class CreateHomeworkSerializer(serializers.ModelSerializer):
    problems = serializers.ListField(
        child=serializers.DictField(),
        write_only=True
    )
    student_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = HomeworkAssignment
        fields = ['title', 'description', 'due_date', 'problems', 'student_ids',
                  'allow_late_submission', 'late_penalty_percent', 'max_attempts']
    
    def validate_due_date(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Due date must be in the future")
        return value
    
    def validate_problems(self, value):
        if not value:
            raise serializers.ValidationError("At least one problem is required")
        
        problem_ids = [p.get('problem_id') for p in value]
        if not all(problem_ids):
            raise serializers.ValidationError("Each problem must have a problem_id")
            
        # Check if all problems exist
        existing_problems = Problem.objects.filter(id__in=problem_ids).count()
        if existing_problems != len(problem_ids):
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
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_avatar = serializers.SerializerMethodField()
    replies_count = serializers.IntegerField(source='replies.count', read_only=True)
    
    class Meta:
        model = HomeworkComment
        fields = ['id', 'homework', 'author', 'author_username', 'author_avatar', 'content',
                  'created_at', 'updated_at', 'is_pinned', 'parent', 'replies_count']
        read_only_fields = ['author']
    
    def get_author_avatar(self, obj):
        if hasattr(obj.author, 'userprofile') and obj.author.userprofile.avatar:
            avatar_path = obj.author.userprofile.avatar
            request = self.context.get('request')
            if request and not avatar_path.startswith('http'):
                return request.build_absolute_uri(avatar_path)
            return avatar_path
        return None


class CreateCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeworkComment
        fields = ['homework', 'content', 'parent']
        
    def validate_homework(self, value):
        # Check if user has access to this homework
        user = self.context['request'].user
        if not (user.is_admin_role() or 
                StudentHomework.objects.filter(student=user, homework=value).exists()):
            raise serializers.ValidationError("You don't have access to this homework")
        return value