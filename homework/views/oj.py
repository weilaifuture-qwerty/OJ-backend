from django.db import transaction
from django.db.models import Q, Count, F, Sum
from django.utils import timezone

from account.decorators import login_required
from submission.models import Submission, JudgeStatus
from utils.api.api import APIView, validate_serializer

from ..models import (
    HomeworkAssignment, HomeworkProblem, StudentHomework,
    HomeworkSubmission, HomeworkComment
)
from ..serializers import (
    StudentHomeworkListSerializer, StudentHomeworkDetailSerializer,
    HomeworkSubmissionSerializer, SubmitHomeworkSerializer,
    HomeworkCommentSerializer, CreateCommentSerializer
)


class StudentHomeworkListAPI(APIView):
    """GET /api/student_homework - Get student's homework list"""
    
    @login_required
    def get(self, request):
        """Get all homework assigned to the student with filtering"""
        status_filter = request.GET.get('status')
        
        homework = StudentHomework.objects.filter(
            student=request.user
        ).select_related('homework', 'homework__created_by').order_by('-homework__due_date')
        
        # Apply status filter
        if status_filter and status_filter != 'all':
            homework = homework.filter(status=status_filter)
        
        # Update status for overdue homework
        now = timezone.now()
        for hw in homework:
            if hw.homework.due_date < now and hw.status in ['assigned', 'in_progress']:
                hw.status = 'late' if hw.homework.allow_late_submission else 'overdue'
                hw.save()
        
        # Use the StudentHomeworkListSerializer for proper response format
        serialized_data = self.paginate_data(request, homework, StudentHomeworkListSerializer)
        
        return self.success(serialized_data)


class HomeworkProgressCountsAPI(APIView):
    """GET /api/homework_progress - Get homework progress counts"""
    
    @login_required
    def get(self, request):
        """Get counts of homework by status"""
        counts = {
            'assigned': 0,
            'in_progress': 0,
            'submitted': 0,
            'graded': 0
        }
        
        # Get status counts
        status_counts = StudentHomework.objects.filter(
            student=request.user
        ).values('status').annotate(count=Count('status'))
        
        for item in status_counts:
            if item['status'] in counts:
                counts[item['status']] = item['count']
        
        return self.success({'counts': counts})


class StudentHomeworkDetailAPI(APIView):
    """GET /api/student_homework_detail - Get detailed homework information"""
    
    @login_required
    def get(self, request, homework_id=None):
        """Get homework details with problems and submissions"""
        # Support both query parameter and URL parameter
        if not homework_id:
            homework_id = request.GET.get('id')
        
        if not homework_id:
            return self.error("Homework ID is required")
        
        try:
            student_homework = StudentHomework.objects.select_related(
                'homework', 'homework__created_by'
            ).get(
                id=homework_id,
                student=request.user
            )
        except StudentHomework.DoesNotExist:
            return self.error("Homework not found or not assigned to you")
        
        # Mark as started if viewing for the first time
        if not student_homework.started_at and student_homework.status == 'assigned':
            student_homework.started_at = timezone.now()
            student_homework.status = 'in_progress'
            student_homework.save()
        
        # Use the detail serializer for proper response format
        try:
            # Build response data manually to avoid serializer issues
            homework = student_homework.homework
            
            # Get problems
            homework_problems = HomeworkProblem.objects.filter(
                homework=homework
            ).select_related('problem').order_by('order')
            
            problems_data = []
            for hp in homework_problems:
                # Check for submissions
                submission = HomeworkSubmission.objects.filter(
                    student_homework=student_homework,
                    problem=hp.problem
                ).first()
                
                problem_data = {
                    'id': hp.id,
                    'problem_id': hp.problem.id,
                    '_id': hp.problem._id,
                    'title': hp.problem.title,
                    'difficulty': hp.problem.difficulty,
                    'score': hp.points,
                    'status': 'not_started',
                    'attempts': 0,
                    'order': hp.order
                }
                
                if submission:
                    problem_data['attempts'] = submission.attempts
                    problem_data['status'] = 'solved' if submission.is_accepted else 'attempted'
                
                problems_data.append(problem_data)
            
            # Calculate total score
            total_possible_score = sum(hp.points for hp in homework_problems)
            
            # Build response
            response_data = {
                'id': student_homework.id,
                'title': homework.title,
                'description': homework.description,
                'due_date': homework.due_date.isoformat() if homework.due_date else None,
                'status': student_homework.status,
                'problems': problems_data,
                'created_at': homework.created_at.isoformat() if homework.created_at else None,
                'max_attempts': None if homework.max_attempts == 0 else homework.max_attempts,
                'late_penalty_percent': homework.late_penalty_percent,
                'feedback': student_homework.feedback or '',
                'total_score': total_possible_score,
                'earned_score': student_homework.total_score
            }
            
            return self.success(response_data)
            
        except Exception as e:
            import traceback
            print(f"Error in StudentHomeworkDetailAPI: {str(e)}")
            traceback.print_exc()
            # Return more detailed error in development
            return self.error(f"Error loading homework: {str(e)}")


class SubmitHomeworkProblemAPI(APIView):
    """POST /api/submit_homework_problem - Submit solution for homework problem"""
    
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
            if student_homework.status != 'late':
                student_homework.status = 'late'
                student_homework.save()
        
        # Get the submission from main submission table
        try:
            submission = Submission.objects.get(
                id=data['submission_id'],
                user_id=request.user.id,
                problem_id=data['problem_id']
            )
        except Submission.DoesNotExist:
            return self.error("Submission not found")
        
        # Check if problem is part of this homework
        try:
            homework_problem = HomeworkProblem.objects.get(
                homework=student_homework.homework,
                problem_id=data['problem_id']
            )
        except HomeworkProblem.DoesNotExist:
            return self.error("Problem not found in this homework")
        
        # Check max attempts
        existing_submission = HomeworkSubmission.objects.filter(
            student_homework=student_homework,
            problem_id=data['problem_id']
        ).first()
        
        if student_homework.homework.max_attempts > 0:
            current_attempts = existing_submission.attempts if existing_submission else 0
            if current_attempts >= student_homework.homework.max_attempts:
                return self.error(f"Maximum attempts ({student_homework.homework.max_attempts}) reached")
        
        with transaction.atomic():
            # Create or update homework submission
            is_accepted = (submission.result == JudgeStatus.ACCEPTED)
            
            if existing_submission:
                # Update existing submission
                existing_submission.submission_id = str(submission.id)
                existing_submission.is_accepted = is_accepted
                existing_submission.attempts += 1
                existing_submission.submitted_at = timezone.now()
                
                # Update score if accepted
                if is_accepted:
                    score = homework_problem.points
                    # Apply late penalty if applicable
                    if student_homework.status == 'late':
                        penalty = student_homework.homework.late_penalty_percent
                        score *= (1 - penalty / 100)
                    existing_submission.score = score
                
                existing_submission.save()
            else:
                # Create new submission
                score = 0
                if is_accepted:
                    score = homework_problem.points
                    # Apply late penalty if applicable
                    if student_homework.status == 'late':
                        penalty = student_homework.homework.late_penalty_percent
                        score *= (1 - penalty / 100)
                
                HomeworkSubmission.objects.create(
                    student_homework=student_homework,
                    problem_id=data['problem_id'],
                    submission_id=str(submission.id),
                    is_accepted=is_accepted,
                    score=score,
                    attempts=1
                )
            
            # Update student homework status if needed
            if student_homework.status == 'in_progress':
                # Check if all required problems are completed
                required_problems = HomeworkProblem.objects.filter(
                    homework=student_homework.homework,
                    required=True
                ).count()
                
                completed_required = HomeworkSubmission.objects.filter(
                    student_homework=student_homework,
                    is_accepted=True
                ).filter(
                    problem__in=HomeworkProblem.objects.filter(
                        homework=student_homework.homework,
                        required=True
                    ).values_list('problem', flat=True)
                ).count()
                
                if required_problems > 0 and completed_required >= required_problems:
                    student_homework.status = 'submitted'
                    student_homework.submitted_at = timezone.now()
                    
                    # Auto-grade if enabled
                    auto_grade = getattr(student_homework.homework, 'auto_grade', True)
                    if auto_grade:
                        total_score = HomeworkSubmission.objects.filter(
                            student_homework=student_homework,
                            is_accepted=True
                        ).aggregate(total=Sum('score'))['total'] or 0
                        
                        max_score = HomeworkProblem.objects.filter(
                            homework=student_homework.homework
                        ).aggregate(total=Sum('points'))['total'] or 100
                        
                        student_homework.total_score = total_score
                        student_homework.max_possible_score = max_score
                        student_homework.grade_percent = (total_score / max_score * 100) if max_score > 0 else 0
                        student_homework.status = 'graded'
                        student_homework.graded_at = timezone.now()
                    
                    student_homework.save()
        
        return self.success({'message': 'Submission recorded'})


class HomeworkSubmitProblemAPI(APIView):
    """POST /api/homework/{hw_id}/submit/{prob_id} - RESTful submit endpoint"""
    
    @login_required
    def post(self, request, hw_id, prob_id):
        """Submit solution for a specific homework problem"""
        # Get student homework
        try:
            student_homework = StudentHomework.objects.get(
                homework_id=hw_id,
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
            if student_homework.status != 'late':
                student_homework.status = 'late'
                student_homework.save()
        
        # Get submission_id from request body
        submission_id = request.data.get('submission_id')
        if not submission_id:
            return self.error("Submission ID is required")
        
        # Get the submission from main submission table
        try:
            submission = Submission.objects.get(
                id=submission_id,
                user_id=request.user.id,
                problem_id=prob_id
            )
        except Submission.DoesNotExist:
            return self.error("Submission not found")
        
        # Check if problem is part of this homework
        try:
            homework_problem = HomeworkProblem.objects.get(
                homework_id=hw_id,
                problem_id=prob_id
            )
        except HomeworkProblem.DoesNotExist:
            return self.error("Problem not found in this homework")
        
        # Check max attempts
        existing_submission = HomeworkSubmission.objects.filter(
            student_homework=student_homework,
            problem_id=prob_id
        ).first()
        
        if student_homework.homework.max_attempts > 0:
            current_attempts = existing_submission.attempts if existing_submission else 0
            if current_attempts >= student_homework.homework.max_attempts:
                return self.error(f"Maximum attempts ({student_homework.homework.max_attempts}) reached")
        
        with transaction.atomic():
            # Create or update homework submission
            is_accepted = (submission.result == JudgeStatus.ACCEPTED)
            
            if existing_submission:
                # Update existing submission
                existing_submission.submission_id = str(submission.id)
                existing_submission.is_accepted = is_accepted
                existing_submission.attempts += 1
                existing_submission.submitted_at = timezone.now()
                
                # Update score if accepted
                if is_accepted:
                    score = homework_problem.points
                    # Apply late penalty if applicable
                    if student_homework.status == 'late':
                        penalty = student_homework.homework.late_penalty_percent
                        score *= (1 - penalty / 100)
                    existing_submission.score = score
                
                existing_submission.save()
            else:
                # Create new submission
                score = 0
                if is_accepted:
                    score = homework_problem.points
                    # Apply late penalty if applicable
                    if student_homework.status == 'late':
                        penalty = student_homework.homework.late_penalty_percent
                        score *= (1 - penalty / 100)
                
                HomeworkSubmission.objects.create(
                    student_homework=student_homework,
                    problem_id=prob_id,
                    submission_id=str(submission.id),
                    is_accepted=is_accepted,
                    score=score,
                    attempts=1
                )
            
            # Update student homework status if needed
            if student_homework.status == 'in_progress':
                # Check if all required problems are completed
                required_problems = HomeworkProblem.objects.filter(
                    homework=student_homework.homework,
                    required=True
                ).count()
                
                completed_required = HomeworkSubmission.objects.filter(
                    student_homework=student_homework,
                    is_accepted=True
                ).filter(
                    problem__in=HomeworkProblem.objects.filter(
                        homework=student_homework.homework,
                        required=True
                    ).values_list('problem', flat=True)
                ).count()
                
                if required_problems > 0 and completed_required >= required_problems:
                    student_homework.status = 'submitted'
                    student_homework.submitted_at = timezone.now()
                    
                    # Auto-grade if enabled
                    auto_grade = getattr(student_homework.homework, 'auto_grade', True)
                    if auto_grade:
                        total_score = HomeworkSubmission.objects.filter(
                            student_homework=student_homework,
                            is_accepted=True
                        ).aggregate(total=Sum('score'))['total'] or 0
                        
                        max_score = HomeworkProblem.objects.filter(
                            homework=student_homework.homework
                        ).aggregate(total=Sum('points'))['total'] or 100
                        
                        student_homework.total_score = total_score
                        student_homework.max_possible_score = max_score
                        student_homework.grade_percent = (total_score / max_score * 100) if max_score > 0 else 0
                        student_homework.status = 'graded'
                        student_homework.graded_at = timezone.now()
                    
                    student_homework.save()
        
        return self.success({
            'message': 'Submission recorded',
            'status': student_homework.status,
            'is_accepted': is_accepted,
            'score': existing_submission.score if existing_submission else score
        })


class HomeworkSubmissionsListAPI(APIView):
    """GET /api/homework/{hw_id}/submissions - Get all submissions for a homework"""
    
    @login_required
    def get(self, request, hw_id):
        """Get all submissions for a specific homework"""
        # Get student homework
        try:
            student_homework = StudentHomework.objects.get(
                homework_id=hw_id,
                student=request.user
            )
        except StudentHomework.DoesNotExist:
            return self.error("Homework not assigned to you")
        
        # Get all submissions for this homework
        submissions = HomeworkSubmission.objects.filter(
            student_homework=student_homework
        ).select_related('problem').order_by('problem__homeworkproblem__order')
        
        submission_data = []
        for sub in submissions:
            # Get the latest submission from main submission table
            latest_submission = None
            if sub.submission_id:
                try:
                    latest_submission = Submission.objects.get(id=sub.submission_id)
                except Submission.DoesNotExist:
                    pass
            
            submission_data.append({
                'problem_id': sub.problem.id,
                'problem_title': sub.problem.title,
                'is_accepted': sub.is_accepted,
                'attempts': sub.attempts,
                'score': sub.score,
                'submitted_at': sub.submitted_at.isoformat() if sub.submitted_at else None,
                'submission_id': sub.submission_id,
                'result': latest_submission.result if latest_submission else None,
                'language': latest_submission.language if latest_submission else None,
                'statistic_info': latest_submission.statistic_info if latest_submission else None
            })
        
        return self.success({
            'homework_id': hw_id,
            'student_homework_id': student_homework.id,
            'status': student_homework.status,
            'submissions': submission_data,
            'total_score': student_homework.total_score,
            'grade_percent': student_homework.grade_percent
        })


class HomeworkCommentsAPI(APIView):
    """Handle homework comments"""
    
    @login_required
    def get(self, request):
        """GET /api/homework_comments - Get comments for a homework"""
        # Log what parameters were received for debugging
        print(f"HomeworkCommentsAPI - Received params: {dict(request.GET)}")
        
        # Try multiple parameter names for compatibility
        param_id = request.GET.get('homework_id') or request.GET.get('id')
        if not param_id:
            return self.error("Homework ID is required", err="missing-homework-id")
        
        # Convert to integer
        try:
            param_id = int(param_id)
        except ValueError:
            return self.error("Invalid homework ID")
        
        # Check if user has access to this homework
        if not request.user.is_admin_role():
            # First, try to find by StudentHomework ID
            student_hw = StudentHomework.objects.filter(
                id=param_id,
                student=request.user
            ).first()
            
            if student_hw:
                # If found, use the actual homework ID
                homework_id = student_hw.homework.id
                print(f"Found StudentHomework ID {param_id}, using homework ID {homework_id}")
            else:
                # Otherwise, assume it's a homework ID
                homework_id = param_id
                print(f"Trying as homework ID {homework_id}")
                
                # Check access
                if not StudentHomework.objects.filter(
                    homework__id=homework_id,
                    student=request.user
                ).exists():
                    return self.error("You don't have access to this homework")
        else:
            # Admin can access any homework
            homework_id = param_id
        
        comments = HomeworkComment.objects.filter(
            homework_id=homework_id,
            parent__isnull=True  # Only top-level comments
        ).select_related('author', 'author__userprofile').prefetch_related(
            'replies__author__userprofile'
        ).order_by('-is_pinned', '-created_at')
        
        # Serialize comments
        serializer = HomeworkCommentSerializer(
            comments, 
            many=True,
            context={'request': request}
        )
        
        return self.success(serializer.data)
    
    @login_required
    @validate_serializer(CreateCommentSerializer)
    def post(self, request):
        """POST /api/homework_comments - Create a new comment"""
        serializer = CreateCommentSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            comment = serializer.save(author=request.user)
            response_serializer = HomeworkCommentSerializer(
                comment,
                context={'request': request}
            )
            return self.success({
                'id': comment.id,
                'message': 'Comment added successfully'
            })
        
        return self.error(serializer.errors)
    
    @login_required
    def delete(self, request):
        """DELETE /api/homework_comments - Delete a comment"""
        comment_id = request.GET.get('id')
        if not comment_id:
            return self.error("Comment ID is required")
        
        try:
            comment = HomeworkComment.objects.get(id=comment_id)
            
            # Check permission
            if comment.author != request.user and not request.user.is_admin_role():
                return self.error("You don't have permission to delete this comment")
            
            comment.delete()
            return self.success({'message': 'Comment deleted successfully'})
            
        except HomeworkComment.DoesNotExist:
            return self.error("Comment not found")