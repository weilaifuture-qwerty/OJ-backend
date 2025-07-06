from django.contrib.auth.models import AbstractBaseUser
from django.conf import settings
from django.db import models
from utils.models import JSONField
from datetime import date, timedelta


class AdminType(object):
    REGULAR_USER = "Regular User"
    ADMIN = "Admin"
    SUPER_ADMIN = "Super Admin"


class ProblemPermission(object):
    NONE = "None"
    OWN = "Own"
    ALL = "All"


class UserManager(models.Manager):
    use_in_migrations = True

    def get_by_natural_key(self, username):
        return self.get(**{f"{self.model.USERNAME_FIELD}__iexact": username})


class User(AbstractBaseUser):
    username = models.TextField(unique=True)
    email = models.TextField(null=True)
    create_time = models.DateTimeField(auto_now_add=True, null=True)
    # One of UserType
    admin_type = models.TextField(default=AdminType.REGULAR_USER)
    problem_permission = models.TextField(default=ProblemPermission.NONE)
    reset_password_token = models.TextField(null=True)
    reset_password_token_expire_time = models.DateTimeField(null=True)
    # SSO auth token
    auth_token = models.TextField(null=True)
    two_factor_auth = models.BooleanField(default=False)
    tfa_token = models.TextField(null=True)
    session_keys = JSONField(default=list)
    # open api key
    open_api = models.BooleanField(default=False)
    open_api_appkey = models.TextField(null=True)
    is_disabled = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def is_admin(self):
        return self.admin_type == AdminType.ADMIN

    def is_super_admin(self):
        return self.admin_type == AdminType.SUPER_ADMIN

    def is_admin_role(self):
        return self.admin_type in [AdminType.ADMIN, AdminType.SUPER_ADMIN]

    def can_mgmt_all_problem(self):
        return self.problem_permission == ProblemPermission.ALL

    def is_contest_admin(self, contest):
        return self.is_authenticated and (contest.created_by == self or self.admin_type == AdminType.SUPER_ADMIN)

    class Meta:
        db_table = "user"


class UserProfile(models.Model):
    STATUS_CHOICES = [
        ('practicing', 'Practicing'),
        ('learning', 'Learning'),
        ('competing', 'In Contest'),
        ('debugging', 'Debugging'),
        ('reviewing', 'Reviewing'),
        ('resting', 'Taking Break')
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # acm_problems_status examples:
    # {
    #     "problems": {
    #         "1": {
    #             "status": JudgeStatus.ACCEPTED,
    #             "_id": "1000"
    #         }
    #     },
    #     "contest_problems": {
    #         "1": {
    #             "status": JudgeStatus.ACCEPTED,
    #             "_id": "1000"
    #         }
    #     }
    # }
    acm_problems_status = JSONField(default=dict)
    # like acm_problems_status, merely add "score" field
    oi_problems_status = JSONField(default=dict)

    real_name = models.TextField(null=True)
    avatar = models.TextField(default=f"{settings.AVATAR_URI_PREFIX}/default.png")
    blog = models.URLField(null=True)
    mood = models.TextField(null=True)
    github = models.TextField(null=True)
    school = models.TextField(null=True)
    major = models.TextField(null=True)
    language = models.TextField(null=True)
    student_group = models.CharField(max_length=100, blank=True, null=True)  # Student group/class
    # for ACM
    accepted_number = models.IntegerField(default=0)
    # for OI
    total_score = models.BigIntegerField(default=0)
    submission_number = models.IntegerField(default=0)
    
    # Status System Fields
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='practicing'
    )
    status_message = models.CharField(max_length=100, blank=True, null=True)  # Status message (renamed from mood to avoid conflict)
    mood_emoji = models.CharField(max_length=10, blank=True, null=True)  # Emoji
    mood_clear_at = models.DateTimeField(blank=True, null=True)  # Auto-clear time
    status_color = models.CharField(max_length=7, default='#52c41a')  # Hex color

    def add_accepted_problem_number(self):
        self.accepted_number = models.F("accepted_number") + 1
        self.save()

    def add_submission_number(self):
        self.submission_number = models.F("submission_number") + 1
        self.save()

    # 计算总分时， 应先减掉上次该题所得分数， 然后再加上本次所得分数
    def add_score(self, this_time_score, last_time_score=None):
        last_time_score = last_time_score or 0
        self.total_score = models.F("total_score") - last_time_score + this_time_score
        self.save()

    class Meta:
        db_table = "user_profile"


class UserStreak(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='streak')
    current_streak = models.IntegerField(default=0)
    best_streak = models.IntegerField(default=0)
    last_check_in = models.DateTimeField(null=True, blank=True)
    total_problems_solved = models.IntegerField(default=0)
    check_in_days = JSONField(default=list)  # List of dates in "YYYY-MM-DD" format
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "user_streak"
    
    def check_in(self, user_date=None):
        """Record a daily check-in"""
        from django.utils import timezone
        
        # Use provided date or default to UTC today
        if user_date:
            today = user_date
        else:
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


class DailyCheckIn(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='check_ins')
    check_in_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "daily_check_in"
        unique_together = ('user', 'check_in_date')
        ordering = ['-check_in_date']


class UserPracticeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='practice_profile')
    skill_level = models.FloatField(default=0.5)  # 0-1 scale
    strongest_tags = JSONField(default=list)
    weakest_tags = JSONField(default=list)
    avg_difficulty_solved = models.FloatField(default=0)
    last_analyzed = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "user_practice_profile"


class ProblemRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='problem_recommendations')
    problem_id = models.IntegerField()  # We'll use problem ID instead of ForeignKey to avoid circular imports
    match_score = models.FloatField()
    ai_reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    clicked = models.BooleanField(default=False)
    solved = models.BooleanField(default=False)
    
    class Meta:
        db_table = "problem_recommendation"
        ordering = ['-created_at', '-match_score']
        # Add unique constraint to prevent duplicate problem recommendations for a user
        unique_together = ('user', 'problem_id')


class DailyProblemSuggestion(models.Model):
    """Daily problem suggestions for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    problem_id = models.IntegerField()  # Using problem ID to avoid circular imports
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
    problem_id = models.IntegerField()  # Using problem ID to avoid circular imports
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
