# Add these serializers to account/serializers.py or create new file

from rest_framework import serializers
from .models import UserStreak, DailyProblemSuggestion, ProblemSuggestion, DailyCheckIn
from problem.models import Problem
from problem.serializers import ProblemTagSerializer


class UserStreakSerializer(serializers.ModelSerializer):
    check_in_days = serializers.ListField(read_only=True)
    
    class Meta:
        model = UserStreak
        fields = ['current_streak', 'best_streak', 'last_check_in', 'total_problems_solved', 'check_in_days']


class DailyCheckInSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyCheckIn
        fields = ['check_in_date', 'created_at']


class DailyProblemSuggestionSerializer(serializers.ModelSerializer):
    problem_id = serializers.CharField(source='problem_id')
    title = serializers.SerializerMethodField()
    difficulty = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    
    class Meta:
        model = DailyProblemSuggestion
        fields = ['problem_id', 'title', 'difficulty', 'tags', 'ai_reason', 'suggested_date']
    
    def get_title(self, obj):
        try:
            problem = Problem.objects.get(id=obj.problem_id)
            return problem.title
        except Problem.DoesNotExist:
            return "Unknown Problem"
    
    def get_difficulty(self, obj):
        try:
            problem = Problem.objects.get(id=obj.problem_id)
            return problem.difficulty
        except Problem.DoesNotExist:
            return "Unknown"
    
    def get_tags(self, obj):
        try:
            problem = Problem.objects.get(id=obj.problem_id)
            return [tag.name for tag in problem.tags.all()]
        except Problem.DoesNotExist:
            return []


class ProblemSuggestionSerializer(serializers.ModelSerializer):
    _id = serializers.CharField(source='problem_id')
    title = serializers.SerializerMethodField()
    difficulty = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    
    class Meta:
        model = ProblemSuggestion
        fields = ['_id', 'title', 'difficulty', 'tags', 'ai_reason', 'match_score']
    
    def get_title(self, obj):
        try:
            problem = Problem.objects.get(id=obj.problem_id)
            return problem.title
        except Problem.DoesNotExist:
            return "Unknown Problem"
    
    def get_difficulty(self, obj):
        try:
            problem = Problem.objects.get(id=obj.problem_id)
            return problem.difficulty
        except Problem.DoesNotExist:
            return "Unknown"
    
    def get_tags(self, obj):
        try:
            problem = Problem.objects.get(id=obj.problem_id)
            return [tag.name for tag in problem.tags.all()]
        except Problem.DoesNotExist:
            return []