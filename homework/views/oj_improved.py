# Improved homework views with real submission tracking

from django.db.models import Q, Count
from django.utils import timezone
from account.decorators import login_required
from submission.models import Submission, JudgeStatus
from homework.models import HomeworkAssignment, HomeworkProblem, StudentHomework
from utils.api import APIView


class StudentHomeworkListImprovedAPI(APIView):
    """GET /api/homework/list - Improved list with real submission status"""
    @login_required
    def get(self, request):
        # Get filter parameters
        status_filter = request.GET.get('status', '')
        include_overdue = request.GET.get('include_overdue', 'true').lower() == 'true'
        
        # Get all homework assigned to the student
        queryset = StudentHomework.objects.filter(
            student=request.user
        ).select_related('homework').order_by('-homework__due_date')
        
        # Apply status filter
        if status_filter:
            statuses = [s.strip() for s in status_filter.split(',')]
            queryset = queryset.filter(status__in=statuses)
        
        # Apply overdue filter
        if not include_overdue:
            queryset = queryset.filter(homework__due_date__gte=timezone.now())
        
        homework_list = []
        for sh in queryset:
            homework = sh.homework
            # Get number of problems
            problem_count = homework.problems.count()
            
            # Calculate completion progress based on actual submissions
            completed_problems = 0
            homework_problems = HomeworkProblem.objects.filter(homework=homework)
            
            for hw_problem in homework_problems:
                # Check if student has solved this problem
                is_solved = Submission.objects.filter(
                    user_id=request.user.id,
                    problem_id=hw_problem.problem_id,
                    result=JudgeStatus.ACCEPTED
                ).exists()
                if is_solved:
                    completed_problems += 1
            
            progress = (completed_problems / problem_count * 100) if problem_count > 0 else 0
            
            # Update status based on actual progress
            if sh.status == 'assigned' and progress > 0:
                sh.status = 'in_progress'
                sh.save()
            elif sh.status == 'in_progress' and progress == 100:
                sh.status = 'submitted'
                sh.submitted_at = timezone.now()
                sh.save()
            
            homework_list.append({
                "id": homework.id,
                "title": homework.title,
                "description": homework.description,
                "due_date": homework.due_date.isoformat(),
                "created_by": homework.created_by.username,
                "status": sh.status,
                "problem_count": problem_count,
                "completed_problems": completed_problems,
                "progress": progress,
                "grade": sh.grade_percent if sh.status == 'graded' else None,
                "assigned_at": sh.assigned_at.isoformat(),
                "is_overdue": homework.is_overdue(),
                "allow_late_submission": homework.allow_late_submission,
                "days_left": (homework.due_date - timezone.now()).days if not homework.is_overdue() else 0
            })
        
        return self.success(homework_list)


class StudentHomeworkDetailImprovedAPI(APIView):
    """GET /api/homework/{id} - Homework details with real submission status"""
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
        
        # Mark as started if first time viewing
        if not student_homework.started_at and student_homework.status == 'assigned':
            student_homework.started_at = timezone.now()
            student_homework.status = 'in_progress'
            student_homework.save()
        
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
            last_submission = submissions.order_by('-create_time').first()
            
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
                    
                # Apply late penalty if applicable
                if student_homework.status == 'late':
                    penalty = homework.late_penalty_percent
                    score *= (1 - penalty / 100)
            
            total_score += score
            
            problems.append({
                "id": problem.id,
                "problem_id": problem._id,
                "title": problem.title,
                "difficulty": problem.difficulty,
                "tags": [tag.name for tag in problem.tags.all()],
                "status": "solved" if is_accepted else ("attempted" if attempts > 0 else "not_started"),
                "attempts": attempts,
                "score": score,
                "max_score": hw_problem.points,
                "order": hw_problem.order,
                "required": hw_problem.required,
                "last_submission": last_submission.create_time.isoformat() if last_submission else None
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
            "created_by": homework.created_by.username,
            "status": student_homework.status,
            "progress": progress,
            "total_score": total_score,
            "max_score": max_score,
            "grade_percent": student_homework.grade_percent,
            "problems": problems,
            "is_overdue": homework.is_overdue(),
            "allow_late_submission": homework.allow_late_submission,
            "late_penalty_percent": homework.late_penalty_percent,
            "max_attempts": homework.max_attempts if homework.max_attempts > 0 else None,
            "feedback": student_homework.feedback,
            "started_at": student_homework.started_at.isoformat() if student_homework.started_at else None,
            "submitted_at": student_homework.submitted_at.isoformat() if student_homework.submitted_at else None
        })