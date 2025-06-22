from django.db import transaction
from django.db.models import Q, Count, F
from django.utils import timezone

from account.decorators import login_required
from submission.models import Submission, JudgeStatus
from utils.api import APIView, validate_serializer

from ..models import (
    HomeworkAssignment, HomeworkProblem, StudentHomework,
    HomeworkSubmission, HomeworkComment
)
from ..serializers import (
    StudentHomeworkSerializer, StudentHomeworkDetailSerializer,
    HomeworkSubmissionSerializer, SubmitHomeworkSerializer,
    HomeworkCommentSerializer, CreateCommentSerializer
)


class StudentHomeworkListAPI(APIView):
    """Student endpoint to view their homework assignments"""
    
    @login_required
    def get(self, request):
        """Get all homework assigned to the student"""
        status_filter = request.GET.get('status')
        
        homework = StudentHomework.objects.filter(
            student=request.user
        ).select_related('homework').order_by('-homework__due_date')
        
        if status_filter:
            homework = homework.filter(status=status_filter)
        
        # Update status for overdue homework
        now = timezone.now()
        for hw in homework:
            if hw.homework.due_date < now and hw.status == 'assigned':
                hw.status = 'late'
                hw.save()
        
        return self.success(self.paginate_data(
            request, homework, StudentHomeworkSerializer
        ))


class StudentHomeworkDetailAPI(APIView):
    """Get detailed homework information for a student"""
    
    @login_required
    def get(self, request):
        """Get homework details with problems and submissions"""
        homework_id = request.GET.get('id')
        if not homework_id:
            return self.error("Homework ID is required")
        
        try:
            student_homework = StudentHomework.objects.get(
                homework_id=homework_id,
                student=request.user
            )
        except StudentHomework.DoesNotExist:
            return self.error("Homework not found or not assigned to you")
        
        # Mark as started if not already
        if not student_homework.started_at:
            student_homework.started_at = timezone.now()
            student_homework.status = 'in_progress'
            student_homework.save()
        
        # Get problem completion status
        problems = HomeworkProblem.objects.filter(
            homework=student_homework.homework
        ).select_related('problem').order_by('order')
        
        problem_status = []
        for hp in problems:
            # Check if student has solved this problem
            submission = HomeworkSubmission.objects.filter(
                student_homework=student_homework,
                problem=hp.problem
            ).order_by('-submitted_at').first()
            
            problem_status.append({
                'problem_id': hp.problem.id,
                'problem_title': hp.problem.title,
                'problem_difficulty': hp.problem.difficulty,
                'points': hp.points,
                'required': hp.required,
                'order': hp.order,
                'is_completed': submission.is_accepted if submission else False,
                'attempts': submission.attempts if submission else 0,
                'score': submission.score if submission else 0
            })
        
        data = StudentHomeworkDetailSerializer(student_homework).data
        data['problem_status'] = problem_status
        
        return self.success(data)


class SubmitHomeworkProblemAPI(APIView):
    """Submit solution for a homework problem"""
    
    @login_required
    @validate_serializer(SubmitHomeworkSerializer)
    def post(self, request):
        """Record homework problem submission"""
        data = request.data
        
        # Get student homework
        try:
            student_homework = StudentHomework.objects.get(
                homework_id=data['homework_id'],
                student=request.user
            )
        except StudentHomework.DoesNotExist:
            return self.error("Homework not assigned to you")
        
        # Check if homework is still open
        if student_homework.status == 'graded':
            return self.error("This homework has already been graded")
        
        now = timezone.now()
        if now > student_homework.homework.due_date:
            if not student_homework.homework.allow_late_submission:
                return self.error("Homework is past due date and late submissions are not allowed")
            student_homework.status = 'late'
        
        # Get the submission from main submission table
        try:
            submission = Submission.objects.get(
                id=data['submission_id'],
                user_id=request.user.id,
                problem_id=data['problem_id']
            )
        except Submission.DoesNotExist:
            return self.error("Submission not found")
        
        # Check max attempts
        homework_problem = HomeworkProblem.objects.get(
            homework=student_homework.homework,
            problem_id=data['problem_id']
        )
        
        existing_submission = HomeworkSubmission.objects.filter(
            student_homework=student_homework,
            problem_id=data['problem_id']
        ).first()
        
        if homework_problem.homework.max_attempts > 0:
            current_attempts = existing_submission.attempts if existing_submission else 0
            if current_attempts >= homework_problem.homework.max_attempts:
                return self.error(f"Maximum attempts ({homework_problem.homework.max_attempts}) reached for this problem")
        
        with transaction.atomic():
            # Create or update homework submission
            if existing_submission:
                existing_submission.submission_id = submission.id
                existing_submission.is_accepted = (submission.result == JudgeStatus.ACCEPTED)
                existing_submission.attempts += 1
                existing_submission.submitted_at = timezone.now()
                
                # Update score based on acceptance
                if existing_submission.is_accepted:
                    existing_submission.score = homework_problem.points
                    # Apply late penalty if applicable
                    if student_homework.status == 'late':
                        penalty = student_homework.homework.late_penalty_percent
                        existing_submission.score *= (1 - penalty / 100)
                
                existing_submission.save()
                homework_submission = existing_submission
            else:
                is_accepted = (submission.result == JudgeStatus.ACCEPTED)
                score = homework_problem.points if is_accepted else 0
                
                # Apply late penalty if applicable
                if is_accepted and student_homework.status == 'late':
                    penalty = student_homework.homework.late_penalty_percent
                    score *= (1 - penalty / 100)
                
                homework_submission = HomeworkSubmission.objects.create(
                    student_homework=student_homework,
                    problem_id=data['problem_id'],
                    submission_id=submission.id,
                    is_accepted=is_accepted,
                    score=score,
                    attempts=1
                )
            
            # Update student homework progress
            student_homework.update_status()
        
        return self.success({
            'submission': HomeworkSubmissionSerializer(homework_submission).data,
            'message': 'Submission recorded successfully'
        })


class HomeworkProgressAPI(APIView):
    """Get student's progress on all homework"""
    
    @login_required
    def get(self, request):
        """Get summary of homework progress"""
        student_homework = StudentHomework.objects.filter(
            student=request.user
        ).select_related('homework')
        
        summary = {
            'total_assigned': student_homework.count(),
            'completed': student_homework.filter(status='graded').count(),
            'in_progress': student_homework.filter(status='in_progress').count(),
            'not_started': student_homework.filter(status='assigned').count(),
            'late': student_homework.filter(status='late').count(),
            'average_grade': 0,
            'upcoming_deadlines': []
        }
        
        # Calculate average grade
        graded = student_homework.filter(status='graded', grade_percent__gt=0)
        if graded.exists():
            total_grade = sum(hw.grade_percent for hw in graded)
            summary['average_grade'] = round(total_grade / graded.count(), 2)
        
        # Get upcoming deadlines (next 7 days)
        upcoming = student_homework.filter(
            homework__due_date__gt=timezone.now(),
            homework__due_date__lte=timezone.now() + timezone.timedelta(days=7),
            status__in=['assigned', 'in_progress']
        ).order_by('homework__due_date')[:5]
        
        for hw in upcoming:
            summary['upcoming_deadlines'].append({
                'homework_id': hw.homework.id,
                'title': hw.homework.title,
                'due_date': hw.homework.due_date,
                'progress': hw.calculate_progress(),
                'status': hw.status
            })
        
        return self.success(summary)


class HomeworkCommentsAPI(APIView):
    """Handle homework comments"""
    
    @login_required
    def get(self, request):
        """Get comments for a homework"""
        homework_id = request.GET.get('homework_id')
        if not homework_id:
            return self.error("Homework ID is required")
        
        # Check if user has access to this homework
        if not request.user.is_admin_role():
            try:
                StudentHomework.objects.get(
                    homework_id=homework_id,
                    student=request.user
                )
            except StudentHomework.DoesNotExist:
                return self.error("You don't have access to this homework")
        
        comments = HomeworkComment.objects.filter(
            homework_id=homework_id,
            parent__isnull=True  # Only top-level comments
        ).select_related('author').prefetch_related('replies')
        
        return self.success(self.paginate_data(
            request, comments, HomeworkCommentSerializer
        ))
    
    @login_required
    @validate_serializer(CreateCommentSerializer)
    def post(self, request):
        """Create a new comment"""
        serializer = CreateCommentSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            comment = serializer.save(author=request.user)
            return self.success({
                'comment': HomeworkCommentSerializer(comment).data,
                'message': 'Comment posted successfully'
            })
        
        return self.invalid_serializer(serializer)
    
    @login_required
    def delete(self, request):
        """Delete a comment"""
        comment_id = request.GET.get('id')
        if not comment_id:
            return self.error("Comment ID is required")
        
        try:
            comment = HomeworkComment.objects.get(id=comment_id)
            
            # Check permission
            if comment.author != request.user and not request.user.is_admin_role():
                return self.error("You don't have permission to delete this comment")
            
            comment.delete()
            return self.success("Comment deleted successfully")
            
        except HomeworkComment.DoesNotExist:
            return self.error("Comment not found")