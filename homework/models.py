from django.db import models
from django.utils import timezone
from account.models import User
from problem.models import Problem
from utils.models import JSONField, RichTextField


class AdminStudentRelation(models.Model):
    """Relationship between admin and students"""
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='managed_students')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='managing_admins')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='student_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = "admin_student_relation"
        unique_together = ('admin', 'student')
        
    def __str__(self):
        return f"{self.admin.username} manages {self.student.username}"


class HomeworkAssignment(models.Model):
    """Homework assignment created by admin"""
    title = models.CharField(max_length=255)
    description = RichTextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_homework')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Assignment details
    due_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    # Problems in this homework
    problems = models.ManyToManyField(Problem, through='HomeworkProblem')
    
    # Students assigned to this homework
    assigned_students = models.ManyToManyField(
        User, 
        through='StudentHomework', 
        through_fields=('homework', 'student'),
        related_name='homework_assignments'
    )
    
    # Additional settings
    allow_late_submission = models.BooleanField(default=False)
    late_penalty_percent = models.IntegerField(default=0)  # Percentage penalty per day late
    max_attempts = models.IntegerField(default=0)  # 0 means unlimited
    
    class Meta:
        db_table = "homework_assignment"
        ordering = ['-created_at']
        
    def __str__(self):
        return self.title
    
    def is_overdue(self):
        return timezone.now() > self.due_date


class HomeworkProblem(models.Model):
    """Problems included in a homework assignment"""
    homework = models.ForeignKey(HomeworkAssignment, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    points = models.IntegerField(default=100)  # Points for this problem
    required = models.BooleanField(default=True)  # Is this problem required?
    
    class Meta:
        db_table = "homework_problem"
        unique_together = ('homework', 'problem')
        ordering = ['order']


class StudentHomework(models.Model):
    """Student's assignment to homework"""
    STATUS_CHOICES = (
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('late', 'Late Submission'),
    )
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_homework')
    homework = models.ForeignKey(HomeworkAssignment, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')
    
    # Progress tracking
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    # Grading
    total_score = models.FloatField(default=0)
    max_possible_score = models.FloatField(default=0)
    grade_percent = models.FloatField(default=0)
    graded_at = models.DateTimeField(null=True, blank=True)
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='graded_homework')
    feedback = models.TextField(blank=True)
    
    class Meta:
        db_table = "student_homework"
        unique_together = ('student', 'homework')
        
    def calculate_progress(self):
        """Calculate completion progress"""
        total_problems = self.homework.problems.count()
        if total_problems == 0:
            return 0
            
        completed = HomeworkSubmission.objects.filter(
            student_homework=self,
            is_accepted=True
        ).values('problem').distinct().count()
        
        return (completed / total_problems) * 100
    
    def update_status(self):
        """Update status based on current state"""
        now = timezone.now()
        
        if self.submitted_at:
            if self.submitted_at > self.homework.due_date and not self.homework.allow_late_submission:
                self.status = 'late'
            else:
                self.status = 'submitted'
        elif self.started_at:
            self.status = 'in_progress'
        elif now > self.homework.due_date:
            self.status = 'late'
        
        self.save()


class HomeworkSubmission(models.Model):
    """Individual problem submission for homework"""
    student_homework = models.ForeignKey(StudentHomework, on_delete=models.CASCADE, related_name='submissions')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    submission_id = models.CharField(max_length=32)  # Reference to main submission table
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)
    score = models.FloatField(default=0)
    attempts = models.IntegerField(default=1)
    
    class Meta:
        db_table = "homework_submission"
        ordering = ['-submitted_at']
        
    def __str__(self):
        return f"{self.student_homework.student.username} - {self.problem.title}"


class HomeworkComment(models.Model):
    """Comments on homework by admin or student"""
    homework = models.ForeignKey(HomeworkAssignment, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_pinned = models.BooleanField(default=False)
    
    # For replies
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    class Meta:
        db_table = "homework_comment"
        ordering = ['-is_pinned', '-created_at']