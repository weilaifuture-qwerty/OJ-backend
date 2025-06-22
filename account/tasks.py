import logging
from datetime import timedelta, date
import dramatiq
from django.utils import timezone
from django.db.models import Count

from options.options import SysOptions
from utils.shortcuts import send_email, DRAMATIQ_WORKER_ARGS

logger = logging.getLogger(__name__)


@dramatiq.actor(**DRAMATIQ_WORKER_ARGS(max_retries=3))
def send_email_async(from_name, to_email, to_name, subject, content):
    if not SysOptions.smtp_config:
        return
    try:
        send_email(smtp_config=SysOptions.smtp_config,
                   from_name=from_name,
                   to_email=to_email,
                   to_name=to_name,
                   subject=subject,
                   content=content)
    except Exception as e:
        logger.exception(e)


@dramatiq.actor(**DRAMATIQ_WORKER_ARGS())
def reset_broken_streaks():
    """Reset streaks for users who didn't check in yesterday"""
    from .models import UserStreak, DailyCheckIn
    
    yesterday = date.today() - timedelta(days=1)
    
    # Get users who checked in yesterday
    users_checked_in_yesterday = DailyCheckIn.objects.filter(
        check_in_date=yesterday
    ).values_list('user_id', flat=True)
    
    # Reset streaks for users who didn't check in yesterday
    reset_count = UserStreak.objects.exclude(
        user_id__in=users_checked_in_yesterday
    ).filter(
        last_check_in__date__lt=yesterday,
        current_streak__gt=0
    ).update(current_streak=0)
    
    logger.info(f"Reset {reset_count} broken streaks")
    return reset_count


@dramatiq.actor(**DRAMATIQ_WORKER_ARGS())
def update_user_practice_profiles():
    """Update practice profiles for active users"""
    from .models import User, UserPracticeProfile
    from submission.models import Submission
    
    # Get users who submitted in the last 7 days
    active_users = User.objects.filter(
        submission__create_time__gte=timezone.now() - timedelta(days=7)
    ).distinct()
    
    updated_count = 0
    for user in active_users:
        try:
            analyze_and_update_profile(user)
            updated_count += 1
        except Exception as e:
            logger.error(f"Error updating profile for user {user.id}: {str(e)}")
    
    logger.info(f"Updated {updated_count} user practice profiles")
    return updated_count


def analyze_and_update_profile(user):
    """Analyze and update a single user's practice profile"""
    from .models import UserPracticeProfile
    from submission.models import Submission, JudgeStatus
    from problem.models import Problem, ProblemDifficulty
    
    # Get recent submissions
    recent_submissions = Submission.objects.filter(
        user_id=user.id,
        create_time__gte=timezone.now() - timedelta(days=30)
    ).select_related('problem')
    
    if not recent_submissions.exists():
        return
    
    # Calculate statistics
    solved_problems = recent_submissions.filter(
        result=JudgeStatus.ACCEPTED
    ).values('problem').distinct()
    
    solved_problem_ids = [s['problem'] for s in solved_problems]
    
    # Tag analysis
    tag_counts = {}
    if solved_problem_ids:
        problems_with_tags = Problem.objects.filter(
            id__in=solved_problem_ids
        ).prefetch_related('tags')
        
        for problem in problems_with_tags:
            for tag in problem.tags.all():
                tag_counts[tag.name] = tag_counts.get(tag.name, 0) + 1
    
    strongest_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    strongest_tags = [tag[0] for tag in strongest_tags[:10]]
    
    # Calculate average difficulty
    difficulty_scores = {
        ProblemDifficulty.Low: 0.3,
        ProblemDifficulty.Mid: 0.6,
        ProblemDifficulty.High: 0.9
    }
    
    total_difficulty = 0
    count = 0
    for problem_id in solved_problem_ids:
        problem = Problem.objects.filter(id=problem_id).first()
        if problem and problem.difficulty:
            total_difficulty += difficulty_scores.get(problem.difficulty, 0.5)
            count += 1
    
    avg_difficulty = total_difficulty / count if count > 0 else 0.5
    
    # Calculate skill level
    skill_level = min(1.0, avg_difficulty * 1.2)  # Simple skill calculation
    
    # Update or create profile
    profile, created = UserPracticeProfile.objects.get_or_create(user=user)
    profile.skill_level = skill_level
    profile.strongest_tags = strongest_tags
    profile.avg_difficulty_solved = avg_difficulty
    profile.save()
    
    return profile
