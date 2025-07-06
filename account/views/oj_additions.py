# Add these views to account/views/oj.py

from django.utils import timezone
from django.db.models import Count
from account.decorators import login_required
from account.models import UserStreak, DailyCheckIn
from submission.models import Submission, JudgeStatus
from utils.api import APIView
from datetime import date, timedelta


class UserStreakAPI(APIView):
    """GET /api/user/streak/"""
    @login_required
    def get(self, request):
        user = request.user
        
        # Get or create user streak
        streak, created = UserStreak.objects.get_or_create(user=user)
        
        # Update total problems solved
        total_solved = Submission.objects.filter(
            user_id=user.id,
            result=JudgeStatus.ACCEPTED
        ).values('problem_id').distinct().count()
        
        if streak.total_problems_solved != total_solved:
            streak.total_problems_solved = total_solved
            streak.save()
        
        # Check if streak needs to be reset (missed days)
        if streak.last_check_in:
            days_since_last = (date.today() - streak.last_check_in.date()).days
            if days_since_last > 1:
                # Streak broken
                streak.current_streak = 0
                streak.save()
        
        return self.success({
            "current_streak": streak.current_streak,
            "best_streak": streak.best_streak,
            "last_check_in": streak.last_check_in.isoformat() if streak.last_check_in else None,
            "check_in_days": streak.check_in_days,
            "total_problems_solved": streak.total_problems_solved
        })


class DailyCheckInAPI(APIView):
    """POST /api/user/daily-check-in/"""
    @login_required
    def post(self, request):
        user = request.user
        
        # Debug logging
        print(f"[DEBUG] Check-in request data: {request.data}")
        
        # Get timezone offset from request (in minutes)
        timezone_offset = request.data.get('timezone_offset', 0)
        print(f"[DEBUG] Timezone offset: {timezone_offset}")
        
        # Calculate today's date based on user's timezone
        from datetime import timedelta
        utc_now = timezone.now()
        # Convert offset from minutes to hours and create timedelta
        user_offset = timedelta(minutes=-timezone_offset)  # Negative because JS returns opposite sign
        user_now = utc_now + user_offset
        today = user_now.date()
        
        print(f"[DEBUG] UTC now: {utc_now}")
        print(f"[DEBUG] User local time: {user_now}")
        print(f"[DEBUG] UTC date: {utc_now.date()}")
        print(f"[DEBUG] User local date: {today}")
        
        # Check if user has solved any problem today (in user's timezone)
        start_of_day = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) + user_offset
        end_of_day = start_of_day + timedelta(days=1)
        
        today_submissions = Submission.objects.filter(
            user_id=user.id,
            result=JudgeStatus.ACCEPTED,
            create_time__gte=start_of_day,
            create_time__lt=end_of_day
        ).exists()
        
        if not today_submissions:
            return self.error("You need to solve at least one problem to check in")
        
        # Get or create user streak
        streak, created = UserStreak.objects.get_or_create(user=user)
        
        # Perform check-in with user's local date
        if streak.check_in(user_date=today):
            # Also create a DailyCheckIn record
            DailyCheckIn.objects.get_or_create(
                user=user,
                check_in_date=today
            )
            
            # Check if user completed daily challenge
            from account.models import DailyProblemSuggestion
            daily_suggestion = DailyProblemSuggestion.objects.filter(
                user=user,
                suggested_date=today
            ).first()
            
            if daily_suggestion and not daily_suggestion.is_completed:
                # Check if the daily problem was solved
                daily_solved = Submission.objects.filter(
                    user_id=user.id,
                    problem_id=daily_suggestion.problem_id,
                    result=JudgeStatus.ACCEPTED,
                    create_time__date=today
                ).exists()
                
                if daily_solved:
                    daily_suggestion.is_completed = True
                    daily_suggestion.completed_time = timezone.now()
                    daily_suggestion.save()
            
            return self.success({
                "message": "Daily check-in successful!",
                "current_streak": streak.current_streak,
                "best_streak": streak.best_streak,
                "daily_challenge_completed": daily_suggestion.is_completed if daily_suggestion else False
            })
        else:
            return self.error("You have already checked in today")


class UserPracticeStatsAPI(APIView):
    """GET /api/user/practice-stats/"""
    @login_required
    def get(self, request):
        user = request.user
        
        # Get statistics for the last 30 days
        start_date = date.today() - timedelta(days=30)
        
        # Daily submission counts
        daily_stats = Submission.objects.filter(
            user_id=user.id,
            create_time__date__gte=start_date
        ).extra(
            select={'day': 'date(create_time)'}
        ).values('day').annotate(
            total=Count('id'),
            accepted=Count('id', filter=Q(result=JudgeStatus.ACCEPTED))
        ).order_by('day')
        
        # Problem difficulty distribution
        difficulty_stats = Problem.objects.filter(
            id__in=Submission.objects.filter(
                user_id=user.id,
                result=JudgeStatus.ACCEPTED
            ).values_list('problem_id', flat=True).distinct()
        ).values('difficulty').annotate(
            count=Count('id')
        )
        
        # Most solved tags
        tag_stats = Problem.objects.filter(
            id__in=Submission.objects.filter(
                user_id=user.id,
                result=JudgeStatus.ACCEPTED
            ).values_list('problem_id', flat=True).distinct()
        ).values('tags__name').annotate(
            count=Count('tags__name')
        ).order_by('-count')[:10]
        
        return self.success({
            "daily_stats": list(daily_stats),
            "difficulty_distribution": list(difficulty_stats),
            "top_tags": [{"tag": t['tags__name'], "count": t['count']} 
                        for t in tag_stats if t['tags__name']]
        })