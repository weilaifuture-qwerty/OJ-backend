# Django signals for submission updates

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from submission.models import Submission, JudgeStatus
from homework.models import HomeworkProblem, StudentHomework, HomeworkSubmission
from account.models import UserStreak, DailyProblemSuggestion


@receiver(post_save, sender=Submission)
def update_homework_on_submission(sender, instance, created, **kwargs):
    """
    Signal handler to update homework status when a submission is accepted
    """
    # Only process if submission is accepted
    if instance.result != JudgeStatus.ACCEPTED:
        return
    
    # Check if this problem is part of any homework
    homework_problems = HomeworkProblem.objects.filter(
        problem_id=instance.problem_id
    ).select_related('homework')
    
    if not homework_problems.exists():
        return
    
    # Process each homework that contains this problem
    for hw_problem in homework_problems:
        homework = hw_problem.homework
        
        # Check if student is assigned to this homework
        try:
            student_homework = StudentHomework.objects.get(
                student_id=instance.user_id,
                homework=homework
            )
        except StudentHomework.DoesNotExist:
            continue
        
        # Skip if homework is already graded
        if student_homework.status == 'graded':
            continue
        
        # Create or update homework submission
        hw_submission, created = HomeworkSubmission.objects.get_or_create(
            student_homework=student_homework,
            problem_id=instance.problem_id,
            defaults={
                'submission_id': str(instance.id),
                'is_accepted': True,
                'score': hw_problem.points,
                'attempts': 1
            }
        )
        
        if not created and not hw_submission.is_accepted:
            # Update existing submission
            hw_submission.submission_id = str(instance.id)
            hw_submission.is_accepted = True
            hw_submission.score = hw_problem.points
            hw_submission.submitted_at = timezone.now()
            
            # Apply late penalty if applicable
            if student_homework.status == 'late':
                penalty = homework.late_penalty_percent
                hw_submission.score *= (1 - penalty / 100)
            
            hw_submission.save()
        
        # Check if all required problems are completed
        required_problems = HomeworkProblem.objects.filter(
            homework=homework,
            required=True
        ).count()
        
        if required_problems > 0:
            completed_required = HomeworkSubmission.objects.filter(
                student_homework=student_homework,
                is_accepted=True,
                problem__in=HomeworkProblem.objects.filter(
                    homework=homework,
                    required=True
                ).values_list('problem', flat=True)
            ).count()
            
            # Update status if all required problems are completed
            if completed_required >= required_problems and student_homework.status in ['assigned', 'in_progress']:
                student_homework.status = 'submitted'
                student_homework.submitted_at = timezone.now()
                
                # Auto-grade if enabled
                if homework.auto_grade:
                    from django.db.models import Sum
                    
                    total_score = HomeworkSubmission.objects.filter(
                        student_homework=student_homework,
                        is_accepted=True
                    ).aggregate(total=Sum('score'))['total'] or 0
                    
                    max_score = HomeworkProblem.objects.filter(
                        homework=homework
                    ).aggregate(total=Sum('points'))['total'] or 100
                    
                    student_homework.total_score = total_score
                    student_homework.max_possible_score = max_score
                    student_homework.grade_percent = (total_score / max_score * 100) if max_score > 0 else 0
                    student_homework.status = 'graded'
                    student_homework.graded_at = timezone.now()
                
                student_homework.save()


@receiver(post_save, sender=Submission)
def update_daily_streak_on_submission(sender, instance, created, **kwargs):
    """
    Signal handler to update user streak when a problem is solved
    """
    # Only process if submission is accepted
    if instance.result != JudgeStatus.ACCEPTED:
        return
    
    # Get or create user streak
    from account.models import UserStreak
    streak, _ = UserStreak.objects.get_or_create(user_id=instance.user_id)
    
    # Check if this is the first accepted submission today
    today = timezone.now().date()
    today_str = today.strftime("%Y-%m-%d")
    
    if today_str not in streak.check_in_days:
        # Perform daily check-in
        streak.check_in()
        
        # Increment total problems solved
        streak.total_problems_solved += 1
        streak.save()
    
    # Check if this completes a daily challenge
    daily_suggestion = DailyProblemSuggestion.objects.filter(
        user_id=instance.user_id,
        problem_id=instance.problem_id,
        suggested_date=today
    ).first()
    
    if daily_suggestion and not daily_suggestion.is_completed:
        daily_suggestion.is_completed = True
        daily_suggestion.completed_time = timezone.now()
        daily_suggestion.save()


@receiver(post_save, sender=Submission)
def update_practice_profile_on_submission(sender, instance, created, **kwargs):
    """
    Signal handler to update user practice profile stats
    """
    # Only process if submission is created (not updated)
    if not created:
        return
    
    # Update submission count in user profile
    from account.models import UserProfile
    try:
        profile = UserProfile.objects.get(user_id=instance.user_id)
        profile.add_submission_number()
        
        # If accepted, update accepted count
        if instance.result == JudgeStatus.ACCEPTED:
            profile.add_accepted_problem_number()
    except UserProfile.DoesNotExist:
        pass