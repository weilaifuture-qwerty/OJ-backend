# Add these models to account/models.py

from datetime import date, timedelta

class UserStreak(models.Model):
    """Track user's daily problem-solving streak"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='streak')
    current_streak = models.IntegerField(default=0)
    best_streak = models.IntegerField(default=0)
    last_check_in = models.DateTimeField(null=True, blank=True)
    total_problems_solved = models.IntegerField(default=0)
    check_in_days = JSONField(default=list)  # List of dates in "YYYY-MM-DD" format
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "user_streak"
    
    def check_in(self):
        """Record a daily check-in"""
        from django.utils import timezone
        today = timezone.now().date()
        today_str = today.strftime("%Y-%m-%d")
        
        if today_str in self.check_in_days:
            return False  # Already checked in today
        
        # Add today to check-in days
        self.check_in_days.append(today_str)
        
        # Update streak
        if self.last_check_in:
            last_date = self.last_check_in.date()
            if (today - last_date).days == 1:
                # Consecutive day
                self.current_streak += 1
            elif (today - last_date).days > 1:
                # Streak broken
                self.current_streak = 1
        else:
            self.current_streak = 1
        
        # Update best streak
        if self.current_streak > self.best_streak:
            self.best_streak = self.current_streak
        
        self.last_check_in = timezone.now()
        self.save()
        return True


class DailyProblemSuggestion(models.Model):
    """Daily problem suggestions for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    problem = models.ForeignKey('problem.Problem', on_delete=models.CASCADE)
    suggested_date = models.DateField(default=date.today)
    ai_reason = models.TextField()
    is_completed = models.BooleanField(default=False)
    completed_time = models.DateTimeField(null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "daily_problem_suggestion"
        unique_together = ('user', 'suggested_date')
        indexes = [
            models.Index(fields=['user', 'suggested_date']),
        ]


class ProblemSuggestion(models.Model):
    """AI-powered problem recommendations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    problem = models.ForeignKey('problem.Problem', on_delete=models.CASCADE)
    ai_reason = models.TextField()
    match_score = models.FloatField(default=0.0)  # 0.0 to 1.0
    suggested_time = models.DateTimeField(auto_now_add=True)
    is_viewed = models.BooleanField(default=False)
    is_attempted = models.BooleanField(default=False)
    
    class Meta:
        db_table = "problem_suggestion"
        indexes = [
            models.Index(fields=['user', '-match_score']),
            models.Index(fields=['user', '-suggested_time']),
        ]