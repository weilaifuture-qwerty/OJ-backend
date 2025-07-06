# Add these views to problem/views/oj.py

from django.utils import timezone
from django.db.models import Q, Count
from account.decorators import login_required
from account.models import DailyProblemSuggestion, ProblemSuggestion, UserPracticeProfile
from submission.models import Submission, JudgeStatus
from utils.api import APIView
from rest_framework.response import Response
import random
from datetime import date, timedelta


class DailyProblemSuggestionAPI(APIView):
    """GET /api/problem/daily-suggestion/"""
    @login_required
    def get(self, request):
        user = request.user
        today = date.today()
        
        # Check if we already have a suggestion for today
        try:
            suggestion = DailyProblemSuggestion.objects.get(
                user=user,
                suggested_date=today
            )
            
            # Get problem details
            problem = Problem.objects.get(id=suggestion.problem_id)
            
            return self.success({
                "problem_id": str(problem.id),
                "title": problem.title,
                "difficulty": problem.difficulty,
                "tags": [tag.name for tag in problem.tags.all()],
                "ai_reason": suggestion.ai_reason,
                "suggested_date": suggestion.suggested_date.strftime("%Y-%m-%d")
            })
            
        except DailyProblemSuggestion.DoesNotExist:
            # Generate new suggestion
            suggestion = self._generate_daily_suggestion(user)
            if suggestion:
                problem = Problem.objects.get(id=suggestion.problem_id)
                return self.success({
                    "problem_id": str(problem.id),
                    "title": problem.title,
                    "difficulty": problem.difficulty,
                    "tags": [tag.name for tag in problem.tags.all()],
                    "ai_reason": suggestion.ai_reason,
                    "suggested_date": suggestion.suggested_date.strftime("%Y-%m-%d")
                })
            else:
                return self.error("No suitable problem found for today")
    
    def _generate_daily_suggestion(self, user):
        """Generate a personalized daily problem suggestion"""
        # Get user's practice profile
        try:
            profile = user.practice_profile
            skill_level = profile.skill_level
        except:
            skill_level = 0.5  # Default medium skill
        
        # Get problems user hasn't solved
        solved_problems = Submission.objects.filter(
            user_id=user.id,
            result=JudgeStatus.ACCEPTED
        ).values_list('problem_id', flat=True).distinct()
        
        # Select difficulty based on skill level
        if skill_level < 0.3:
            difficulty = "Low"
        elif skill_level < 0.7:
            difficulty = "Mid"
        else:
            difficulty = "High"
        
        # Find suitable problems
        problems = Problem.objects.filter(
            visible=True,
            contest__isnull=True  # Only non-contest problems
        ).exclude(
            id__in=solved_problems
        )
        
        # Try to find problem of appropriate difficulty
        suitable_problems = problems.filter(difficulty=difficulty)
        if not suitable_problems.exists():
            suitable_problems = problems  # Fall back to any difficulty
        
        if not suitable_problems.exists():
            return None
        
        # Select a random problem
        problem = random.choice(suitable_problems)
        
        # Generate AI reason
        ai_reason = self._generate_ai_reason(user, problem, skill_level)
        
        # Create suggestion
        suggestion = DailyProblemSuggestion.objects.create(
            user=user,
            problem_id=problem.id,
            suggested_date=date.today(),
            ai_reason=ai_reason
        )
        
        return suggestion
    
    def _generate_ai_reason(self, user, problem, skill_level):
        """Generate AI reasoning for why this problem was selected"""
        reasons = []
        
        # Difficulty-based reason
        if problem.difficulty == "Low" and skill_level < 0.3:
            reasons.append("Perfect for building fundamentals")
        elif problem.difficulty == "Mid" and 0.3 <= skill_level < 0.7:
            reasons.append("Good challenge for your current skill level")
        elif problem.difficulty == "High" and skill_level >= 0.7:
            reasons.append("Advanced problem to push your limits")
        else:
            reasons.append("Helps expand your problem-solving range")
        
        # Tag-based reason
        if problem.tags.exists():
            tag_names = [tag.name for tag in problem.tags.all()[:2]]
            reasons.append(f"Good for practicing {' and '.join(tag_names)}")
        
        # Submission stats reason
        if problem.submission_number > 0:
            ac_rate = (problem.accepted_number / problem.submission_number) * 100
            if ac_rate < 30:
                reasons.append("Challenging problem with low acceptance rate")
            elif ac_rate > 70:
                reasons.append("High success rate makes it great for confidence building")
        
        return ". ".join(reasons)


class ProblemSuggestionsAPI(APIView):
    """GET /api/problem/suggestions/"""
    @login_required
    def get(self, request):
        user = request.user
        limit = min(int(request.GET.get('limit', 5)), 10)
        
        # Get existing suggestions from last 7 days
        recent_suggestions = ProblemSuggestion.objects.filter(
            user=user,
            suggested_time__gte=timezone.now() - timedelta(days=7)
        ).order_by('-match_score')[:limit]
        
        if recent_suggestions.count() < limit:
            # Generate new suggestions
            self._generate_suggestions(user, limit - recent_suggestions.count())
            # Re-fetch suggestions
            recent_suggestions = ProblemSuggestion.objects.filter(
                user=user,
                suggested_time__gte=timezone.now() - timedelta(days=7)
            ).order_by('-match_score')[:limit]
        
        suggestions = []
        for suggestion in recent_suggestions:
            try:
                problem = Problem.objects.get(id=suggestion.problem_id)
                suggestions.append({
                    "_id": str(problem._id),
                    "title": problem.title,
                    "difficulty": problem.difficulty,
                    "tags": [tag.name for tag in problem.tags.all()],
                    "ai_reason": suggestion.ai_reason,
                    "match_score": suggestion.match_score
                })
            except Problem.DoesNotExist:
                continue
        
        return self.success({"suggestions": suggestions})
    
    def _generate_suggestions(self, user, count):
        """Generate AI-powered problem suggestions"""
        # Get user's solved problems and preferences
        solved_problems = Submission.objects.filter(
            user_id=user.id,
            result=JudgeStatus.ACCEPTED
        ).values_list('problem_id', flat=True).distinct()
        
        # Get user's most successful tags
        successful_tags = Problem.objects.filter(
            id__in=solved_problems
        ).values('tags__name').annotate(
            count=Count('tags__name')
        ).order_by('-count')[:5]
        
        preferred_tags = [tag['tags__name'] for tag in successful_tags if tag['tags__name']]
        
        # Find unsolved problems
        problems = Problem.objects.filter(
            visible=True,
            contest__isnull=True
        ).exclude(
            id__in=solved_problems
        ).exclude(
            id__in=ProblemSuggestion.objects.filter(
                user=user
            ).values_list('problem_id', flat=True)
        )
        
        # Score and select problems
        scored_problems = []
        for problem in problems:
            score = self._calculate_match_score(problem, user, preferred_tags)
            if score > 0.3:  # Minimum threshold
                scored_problems.append((problem, score))
        
        # Sort by score and take top N
        scored_problems.sort(key=lambda x: x[1], reverse=True)
        
        for problem, score in scored_problems[:count]:
            reason = self._generate_suggestion_reason(problem, user, preferred_tags, score)
            ProblemSuggestion.objects.create(
                user=user,
                problem_id=problem.id,
                match_score=score,
                ai_reason=reason
            )
    
    def _calculate_match_score(self, problem, user, preferred_tags):
        """Calculate how well a problem matches user's profile"""
        score = 0.5  # Base score
        
        # Tag matching
        problem_tags = [tag.name for tag in problem.tags.all()]
        if problem_tags and preferred_tags:
            matching_tags = set(problem_tags) & set(preferred_tags)
            score += len(matching_tags) * 0.1
        
        # Difficulty matching
        try:
            profile = user.practice_profile
            if problem.difficulty == "Low" and profile.skill_level < 0.4:
                score += 0.2
            elif problem.difficulty == "Mid" and 0.3 < profile.skill_level < 0.7:
                score += 0.2
            elif problem.difficulty == "High" and profile.skill_level > 0.6:
                score += 0.2
        except:
            pass
        
        # Acceptance rate factor
        if problem.submission_number > 10:
            ac_rate = problem.accepted_number / problem.submission_number
            if 0.3 < ac_rate < 0.7:  # Not too easy, not too hard
                score += 0.1
        
        return min(score, 1.0)
    
    def _generate_suggestion_reason(self, problem, user, preferred_tags, score):
        """Generate reason for suggestion"""
        reasons = []
        
        # Tag-based reasoning
        problem_tags = [tag.name for tag in problem.tags.all()]
        if problem_tags and preferred_tags:
            matching_tags = set(problem_tags) & set(preferred_tags)
            if matching_tags:
                reasons.append(f"Matches your interest in {', '.join(matching_tags)}")
        
        # Score-based reasoning
        if score > 0.8:
            reasons.append("Highly recommended based on your solving pattern")
        elif score > 0.6:
            reasons.append("Good match for your current progress")
        
        # Problem stats reasoning
        if problem.submission_number > 50:
            reasons.append(f"Popular problem with {problem.submission_number} submissions")
        
        # Difficulty progression
        reasons.append(f"Next step in your {problem.difficulty.lower()} difficulty journey")
        
        return ". ".join(reasons) if reasons else "Recommended for skill development"