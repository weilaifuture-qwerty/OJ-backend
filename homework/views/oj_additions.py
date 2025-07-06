# Add these views to homework/views/oj.py

from django.db.models import Q, Count, Max
from account.decorators import login_required
from submission.models import Submission, JudgeStatus
from homework.models import HomeworkAssignment, HomeworkProblem, StudentHomework, HomeworkComment
from utils.api import APIView, validate_serializer
from homework.serializers import HomeworkCommentSerializer, CreateHomeworkCommentSerializer


class HomeworkProblemStatusAPI(APIView):
    """GET /api/homework/{homework_id}/problem-status/"""
    @login_required
    def get(self, request, homework_id):
        try:
            homework = HomeworkAssignment.objects.get(id=homework_id)
        except HomeworkAssignment.DoesNotExist:
            return self.error("Homework not found")
        
        # Check if user has access to this homework
        if not StudentHomework.objects.filter(student=request.user, homework=homework).exists():
            return self.error("You don't have access to this homework")
        
        # Get all problems in this homework
        homework_problems = HomeworkProblem.objects.filter(homework=homework).select_related('problem')
        
        problem_statuses = []
        for hw_problem in homework_problems:
            problem = hw_problem.problem
            
            # Get submission statistics for this problem
            submissions = Submission.objects.filter(
                user_id=request.user.id,
                problem_id=problem.id
            )
            
            # Check if solved
            is_solved = submissions.filter(result=JudgeStatus.ACCEPTED).exists()
            
            # Get attempt count
            attempt_count = submissions.count()
            
            # Get last submission
            last_submission = submissions.order_by('-create_time').first()
            
            # Calculate best score (for OI mode problems)
            best_score = 0
            if is_solved:
                if problem.rule_type == "OI":
                    # For OI problems, get the highest score
                    best_score_submission = submissions.filter(
                        result=JudgeStatus.ACCEPTED
                    ).order_by('-score').first()
                    if best_score_submission:
                        best_score = best_score_submission.score
                else:
                    # For ACM problems, accepted means full score
                    best_score = hw_problem.points
            
            problem_statuses.append({
                "problem_id": str(problem.id),
                "_id": problem._id,
                "title": problem.title,
                "status": "solved" if is_solved else ("attempted" if attempt_count > 0 else "not_started"),
                "attempts": attempt_count,
                "last_submission": last_submission.create_time.isoformat() if last_submission else None,
                "best_score": best_score,
                "max_score": hw_problem.points,
                "required": hw_problem.required
            })
        
        return self.success({"problems": problem_statuses})


class HomeworkCommentsListAPI(APIView):
    """GET /api/homework/{homework_id}/comments/"""
    @login_required
    def get(self, request, homework_id):
        try:
            homework = HomeworkAssignment.objects.get(id=homework_id)
        except HomeworkAssignment.DoesNotExist:
            return self.error("Homework not found")
        
        # Check access
        if not (StudentHomework.objects.filter(student=request.user, homework=homework).exists() or
                request.user.is_admin_role() or
                homework.created_by == request.user):
            return self.error("You don't have access to this homework")
        
        # Get top-level comments (no parent)
        comments = HomeworkComment.objects.filter(
            homework=homework,
            parent__isnull=True
        ).select_related('author').prefetch_related('replies')
        
        serializer = HomeworkCommentSerializer(comments, many=True)
        return self.success(serializer.data)


class HomeworkCommentCreateAPI(APIView):
    """POST /api/homework/{homework_id}/comments/"""
    @login_required
    @validate_serializer(CreateHomeworkCommentSerializer)
    def post(self, request, homework_id):
        try:
            homework = HomeworkAssignment.objects.get(id=homework_id)
        except HomeworkAssignment.DoesNotExist:
            return self.error("Homework not found")
        
        # Check access
        if not (StudentHomework.objects.filter(student=request.user, homework=homework).exists() or
                request.user.is_admin_role() or
                homework.created_by == request.user):
            return self.error("You don't have access to this homework")
        
        data = request.data
        parent_id = data.get('parent_id')
        
        # Validate parent comment if provided
        parent = None
        if parent_id:
            try:
                parent = HomeworkComment.objects.get(id=parent_id, homework=homework)
            except HomeworkComment.DoesNotExist:
                return self.error("Parent comment not found")
        
        # Create comment
        comment = HomeworkComment.objects.create(
            homework=homework,
            author=request.user,
            content=data['content'],
            parent=parent,
            is_pinned=data.get('is_pinned', False) if request.user.is_admin_role() else False
        )
        
        serializer = HomeworkCommentSerializer(comment)
        return self.success(serializer.data)


class HomeworkCommentDeleteAPI(APIView):
    """DELETE /api/homework/{homework_id}/comments/{comment_id}/"""
    @login_required
    def delete(self, request, homework_id, comment_id):
        try:
            comment = HomeworkComment.objects.get(
                id=comment_id,
                homework_id=homework_id
            )
        except HomeworkComment.DoesNotExist:
            return self.error("Comment not found")
        
        # Check permission - only author or admin can delete
        if comment.author != request.user and not request.user.is_admin_role():
            return self.error("You don't have permission to delete this comment")
        
        comment.delete()
        return self.success("Comment deleted successfully")


class StudentHomeworkDetailFixedAPI(APIView):
    """GET /api/homework/student-detail/{id}/ - Fixed version with real submission status"""
    @login_required  
    def get(self, request, homework_id):
        try:
            homework = HomeworkAssignment.objects.get(id=homework_id)
        except HomeworkAssignment.DoesNotExist:
            return self.error("Homework not found")
        
        # Get student's homework record
        try:
            student_homework = StudentHomework.objects.get(
                student=request.user,
                homework=homework
            )
        except StudentHomework.DoesNotExist:
            return self.error("You are not assigned to this homework")
        
        # Get problems with real submission status
        problems = []
        homework_problems = HomeworkProblem.objects.filter(
            homework=homework
        ).select_related('problem').order_by('order')
        
        total_score = 0
        max_score = 0
        
        for hw_problem in homework_problems:
            problem = hw_problem.problem
            max_score += hw_problem.points
            
            # Get real submission data
            submissions = Submission.objects.filter(
                user_id=request.user.id,
                problem_id=problem.id
            )
            
            is_accepted = submissions.filter(result=JudgeStatus.ACCEPTED).exists()
            attempts = submissions.count()
            
            # Calculate score
            score = 0
            if is_accepted:
                if problem.rule_type == "OI":
                    # Get best score for OI problems
                    best_submission = submissions.filter(
                        result=JudgeStatus.ACCEPTED
                    ).order_by('-score').first()
                    if best_submission:
                        score = min(best_submission.score, hw_problem.points)
                else:
                    # ACM mode - full score if accepted
                    score = hw_problem.points
            
            total_score += score
            
            problems.append({
                "id": problem.id,
                "problem_id": problem._id,
                "title": problem.title,
                "difficulty": problem.difficulty,
                "status": "solved" if is_accepted else ("attempted" if attempts > 0 else "not_started"),
                "attempts": attempts,
                "score": score,
                "max_score": hw_problem.points,
                "order": hw_problem.order,
                "required": hw_problem.required
            })
        
        # Update student homework score
        if student_homework.total_score != total_score:
            student_homework.total_score = total_score
            student_homework.max_possible_score = max_score
            student_homework.grade_percent = (total_score / max_score * 100) if max_score > 0 else 0
            student_homework.save()
        
        # Calculate real progress
        completed_problems = sum(1 for p in problems if p['status'] == 'solved')
        total_problems = len(problems)
        progress = (completed_problems / total_problems * 100) if total_problems > 0 else 0
        
        return self.success({
            "id": homework.id,
            "title": homework.title,
            "description": homework.description,
            "due_date": homework.due_date.isoformat(),
            "status": student_homework.status,
            "progress": progress,
            "total_score": total_score,
            "max_score": max_score,
            "grade_percent": student_homework.grade_percent,
            "problems": problems,
            "is_overdue": homework.is_overdue(),
            "allow_late_submission": homework.allow_late_submission,
            "feedback": student_homework.feedback
        })