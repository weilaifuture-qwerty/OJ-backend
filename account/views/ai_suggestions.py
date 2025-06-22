from datetime import timedelta
from django.db.models import Count, Avg, Q, F
from django.utils import timezone

from submission.models import Submission, JudgeStatus
from problem.models import Problem, ProblemTag, ProblemDifficulty
from utils.api import APIView
from ..decorators import login_required
from ..models import UserPracticeProfile, ProblemRecommendation


class ProblemSuggestionsAPI(APIView):
    @login_required
    def get(self, request):
        """GET /api/problem_suggestions - Get AI-powered problem recommendations"""
        user = request.user
        
        try:
            # Analyze user's practice history
            profile = self.analyze_user_profile(user)
            
            # Get AI recommendations
            suggestions = self.get_ai_recommendations(user, profile)
            
            # Get unique problem IDs and their best recommendations
            seen_problems = set()
            unique_suggestions = []
            for s in suggestions:
                if s.problem_id not in seen_problems:
                    seen_problems.add(s.problem_id)
                    unique_suggestions.append(s)
                if len(unique_suggestions) >= 5:
                    break
            
            # Get problem details for recommendations
            problem_ids = [s.problem_id for s in unique_suggestions]
            problems = Problem.objects.filter(id__in=problem_ids).prefetch_related('tags')
            problem_dict = {p.id: p for p in problems}
            
            suggestion_data = []
            for s in unique_suggestions:
                if s.problem_id in problem_dict:
                    p = problem_dict[s.problem_id]
                    suggestion_data.append({
                        "id": p.id,  # Database ID
                        "_id": p._id,  # Display ID for URL routing
                        "title": p.title,
                        "difficulty": p.difficulty,
                        "accepted_number": p.accepted_number,
                        "submission_number": p.submission_number,
                        "tags": [tag.name for tag in p.tags.all()],
                        "ai_reason": s.ai_reason,
                        "match_score": s.match_score
                    })
            
            return self.success({
                "suggestions": suggestion_data,
                "analysis_metadata": {
                    "analyzed_submissions": profile['total_submissions'],
                    "user_skill_level": profile['skill_level'],
                    "strongest_tags": profile['strongest_tags'][:5],
                    "weakest_tags": profile['weakest_tags'][:5],
                    "recent_difficulty_trend": profile['difficulty_trend']
                }
            })
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in problem suggestions: {str(e)}")
            return self.error(f"An error occurred: {str(e)}")
    
    def analyze_user_profile(self, user):
        """Analyze user's submission history and practice patterns"""
        # Get recent submissions
        recent_submissions = Submission.objects.filter(
            user_id=user.id,
            create_time__gte=timezone.now() - timedelta(days=30)
        ).select_related('problem')
        
        # Calculate statistics
        solved_problems = recent_submissions.filter(
            result=JudgeStatus.ACCEPTED
        ).values('problem').distinct()
        
        solved_problem_ids = [s['problem'] for s in solved_problems]
        
        # Tag analysis - find strongest tags
        tag_stats = []
        if solved_problem_ids:
            problems_with_tags = Problem.objects.filter(
                id__in=solved_problem_ids
            ).prefetch_related('tags')
            
            tag_counts = {}
            for problem in problems_with_tags:
                for tag in problem.tags.all():
                    tag_counts[tag.name] = tag_counts.get(tag.name, 0) + 1
            
            tag_stats = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Find weak areas (tags with low success rate)
        weak_tags = self.find_weak_areas(user, recent_submissions)
        
        # Calculate skill level based on problem difficulty
        skill_level = self.calculate_skill_level(user, solved_problem_ids)
        
        # Analyze difficulty trend
        difficulty_trend = self.analyze_difficulty_trend(recent_submissions)
        
        # Update or create user practice profile
        profile, created = UserPracticeProfile.objects.get_or_create(user=user)
        profile.skill_level = skill_level
        profile.strongest_tags = [tag[0] for tag in tag_stats[:10]]
        profile.weakest_tags = weak_tags[:10]
        profile.avg_difficulty_solved = difficulty_trend.get('avg_difficulty', 0.5)
        profile.save()
        
        return {
            'total_submissions': recent_submissions.count(),
            'skill_level': skill_level,
            'strongest_tags': [tag[0] for tag in tag_stats],
            'weakest_tags': weak_tags,
            'difficulty_trend': difficulty_trend
        }
    
    def find_weak_areas(self, user, recent_submissions):
        """Find tags where user has low success rate"""
        # Get all attempted problems
        attempted_problems = recent_submissions.values('problem').distinct()
        attempted_problem_ids = [s['problem'] for s in attempted_problems]
        
        if not attempted_problem_ids:
            return []
        
        # Get accepted problems
        accepted_problems = recent_submissions.filter(
            result=JudgeStatus.ACCEPTED
        ).values('problem').distinct()
        accepted_problem_ids = [s['problem'] for s in accepted_problems]
        
        # Calculate success rate by tag
        tag_attempts = {}
        tag_successes = {}
        
        problems = Problem.objects.filter(id__in=attempted_problem_ids).prefetch_related('tags')
        for problem in problems:
            for tag in problem.tags.all():
                tag_name = tag.name
                tag_attempts[tag_name] = tag_attempts.get(tag_name, 0) + 1
                if problem.id in accepted_problem_ids:
                    tag_successes[tag_name] = tag_successes.get(tag_name, 0) + 1
        
        # Find tags with low success rate
        weak_tags = []
        for tag, attempts in tag_attempts.items():
            if attempts >= 3:  # Only consider tags with at least 3 attempts
                success_rate = tag_successes.get(tag, 0) / attempts
                if success_rate < 0.5:  # Less than 50% success rate
                    weak_tags.append((tag, success_rate))
        
        weak_tags.sort(key=lambda x: x[1])  # Sort by success rate (ascending)
        return [tag[0] for tag in weak_tags]
    
    def calculate_skill_level(self, user, solved_problem_ids):
        """Calculate user's skill level based on solved problems"""
        if not solved_problem_ids:
            return 0.5  # Default skill level
        
        # Get difficulty distribution of solved problems
        problems = Problem.objects.filter(id__in=solved_problem_ids)
        
        difficulty_scores = {
            ProblemDifficulty.Low: 0.3,
            ProblemDifficulty.Mid: 0.6,
            ProblemDifficulty.High: 0.9
        }
        
        total_score = 0
        count = 0
        
        for problem in problems:
            score = difficulty_scores.get(problem.difficulty, 0.5)
            # Adjust score based on acceptance rate
            if problem.submission_number > 0:
                acceptance_rate = problem.accepted_number / problem.submission_number
                # Harder problems (lower acceptance rate) give more skill points
                score = score * (2 - acceptance_rate)
            total_score += score
            count += 1
        
        return min(1.0, total_score / count) if count > 0 else 0.5
    
    def analyze_difficulty_trend(self, recent_submissions):
        """Analyze the trend in problem difficulty over time"""
        accepted_submissions = recent_submissions.filter(
            result=JudgeStatus.ACCEPTED
        ).select_related('problem').order_by('create_time')
        
        if not accepted_submissions:
            return {'avg_difficulty': 0.5, 'trend': 'stable'}
        
        difficulty_values = {
            ProblemDifficulty.Low: 0.3,
            ProblemDifficulty.Mid: 0.6,
            ProblemDifficulty.High: 0.9
        }
        
        difficulties = []
        for sub in accepted_submissions:
            if sub.problem.difficulty:
                difficulties.append(difficulty_values.get(sub.problem.difficulty, 0.5))
        
        if not difficulties:
            return {'avg_difficulty': 0.5, 'trend': 'stable'}
        
        avg_difficulty = sum(difficulties) / len(difficulties)
        
        # Determine trend
        if len(difficulties) >= 5:
            recent_avg = sum(difficulties[-5:]) / 5
            older_avg = sum(difficulties[:-5]) / len(difficulties[:-5]) if len(difficulties) > 5 else avg_difficulty
            
            if recent_avg > older_avg + 0.1:
                trend = 'increasing'
            elif recent_avg < older_avg - 0.1:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'avg_difficulty': avg_difficulty,
            'trend': trend
        }
    
    def get_ai_recommendations(self, user, profile):
        """Generate AI-powered problem recommendations"""
        # Delete old recommendations
        ProblemRecommendation.objects.filter(
            user=user,
            created_at__lt=timezone.now() - timedelta(days=7)
        ).delete()
        
        # Check if we have recent recommendations
        recent_recommendations = ProblemRecommendation.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timedelta(hours=6)
        ).values('problem_id').distinct().order_by('-match_score')
        
        # Get distinct problem IDs from recent recommendations
        if recent_recommendations.count() >= 5:
            # Get the actual recommendation objects with distinct problem_ids
            problem_ids = [r['problem_id'] for r in recent_recommendations[:10]]
            return list(ProblemRecommendation.objects.filter(
                user=user,
                problem_id__in=problem_ids,
                created_at__gte=timezone.now() - timedelta(hours=6)
            ).order_by('-match_score')[:10])
        
        # Get solved problem IDs
        solved_problem_ids = Submission.objects.filter(
            user_id=user.id,
            result=JudgeStatus.ACCEPTED
        ).values_list('problem_id', flat=True).distinct()
        
        # Get already recommended problem IDs to avoid duplicates
        already_recommended = ProblemRecommendation.objects.filter(
            user=user
        ).values_list('problem_id', flat=True).distinct()
        
        # Get candidate problems (not solved, visible, not already recommended)
        candidates = Problem.objects.filter(
            visible=True
        ).exclude(
            id__in=solved_problem_ids
        ).exclude(
            id__in=already_recommended
        ).prefetch_related('tags').distinct()[:100]  # Limit to 100 candidates for performance
        
        recommendations = []
        
        for problem in candidates:
            score, reason = self.calculate_match_score(problem, profile)
            
            rec = ProblemRecommendation(
                user=user,
                problem_id=problem.id,
                match_score=score,
                ai_reason=reason
            )
            recommendations.append(rec)
        
        # Sort by match score
        recommendations.sort(key=lambda x: x.match_score, reverse=True)
        
        # Save top recommendations
        if recommendations:
            # Update existing or create new recommendations
            for rec in recommendations[:20]:
                ProblemRecommendation.objects.update_or_create(
                    user=rec.user,
                    problem_id=rec.problem_id,
                    defaults={
                        'match_score': rec.match_score,
                        'ai_reason': rec.ai_reason,
                        'created_at': timezone.now()
                    }
                )
        
        # Return all recommendations for this user (including new ones)
        return list(ProblemRecommendation.objects.filter(
            user=user
        ).order_by('-match_score')[:10])
    
    def calculate_match_score(self, problem, profile):
        """Calculate how well a problem matches user's profile"""
        score = 0.5  # Base score
        reasons = []
        
        # Difficulty matching
        difficulty_values = {
            ProblemDifficulty.Low: 0.3,
            ProblemDifficulty.Mid: 0.6,
            ProblemDifficulty.High: 0.9
        }
        
        problem_difficulty = difficulty_values.get(problem.difficulty, 0.5)
        user_skill = profile['skill_level']
        
        # Optimal difficulty is slightly above user's current level
        optimal_difficulty = min(1.0, user_skill + 0.2)
        difficulty_diff = abs(problem_difficulty - optimal_difficulty)
        
        if difficulty_diff < 0.1:
            score += 0.3
            reasons.append("Perfect difficulty match for your skill level")
        elif difficulty_diff < 0.2:
            score += 0.2
            reasons.append("Good difficulty match")
        elif problem_difficulty > user_skill + 0.4:
            score -= 0.2
            reasons.append("May be too challenging")
        elif problem_difficulty < user_skill - 0.3:
            score -= 0.1
            reasons.append("May be too easy")
        
        # Tag matching
        problem_tags = [tag.name for tag in problem.tags.all()]
        
        # Boost score for weak areas (learning opportunity)
        weak_tag_matches = set(problem_tags) & set(profile['weakest_tags'])
        if weak_tag_matches:
            score += 0.2
            reasons.append(f"Good practice for weak areas: {', '.join(weak_tag_matches)}")
        
        # Moderate boost for strong areas (confidence building)
        strong_tag_matches = set(problem_tags) & set(profile['strongest_tags'][:10])
        if strong_tag_matches:
            score += 0.1
            reasons.append(f"Matches your strengths: {', '.join(strong_tag_matches)}")
        
        # Problem popularity (acceptance rate as quality indicator)
        if problem.submission_number > 10:
            acceptance_rate = problem.accepted_number / problem.submission_number
            if 0.3 < acceptance_rate < 0.7:  # Not too easy, not too hard
                score += 0.1
                reasons.append(f"Well-balanced problem ({int(acceptance_rate * 100)}% acceptance rate)")
        
        # Ensure score is between 0 and 1
        score = max(0, min(1, score))
        
        # Generate final reason
        if not reasons:
            reasons.append("Standard recommendation based on your profile")
        
        reason = "; ".join(reasons)
        
        return score, reason


class UserPracticeHistoryAPI(APIView):
    @login_required
    def get(self, request):
        """GET /api/user_practice_history - Get user's practice history and statistics"""
        try:
            days = int(request.GET.get('days', 30))
            limit = int(request.GET.get('limit', 100))
            
            # Validate parameters
            days = min(365, max(1, days))
            limit = min(1000, max(1, limit))
            
            # Get base queryset without slicing for statistics
            base_submissions = Submission.objects.filter(
                user_id=request.user.id,
                create_time__gte=timezone.now() - timedelta(days=days)
            )
            
            # Get sliced submissions for display
            submissions = base_submissions.select_related('problem').order_by('-create_time')[:limit]
            
            # Calculate statistics using the base queryset
            total_problems_solved = Submission.objects.filter(
                user_id=request.user.id,
                result=JudgeStatus.ACCEPTED
            ).values('problem').distinct().count()
            
            recent_accepted = base_submissions.filter(result=JudgeStatus.ACCEPTED).count()
            recent_total = base_submissions.count()
            recent_acceptance_rate = recent_accepted / recent_total if recent_total > 0 else 0
            
            # Get difficulty distribution
            difficulty_dist = {}
            accepted_problems = base_submissions.filter(
                result=JudgeStatus.ACCEPTED
            ).values('problem_id').distinct()
            
            if accepted_problems:
                problems = Problem.objects.filter(
                    id__in=[p['problem_id'] for p in accepted_problems]
                )
                for problem in problems:
                    diff = problem.difficulty or 'Unknown'
                    difficulty_dist[diff] = difficulty_dist.get(diff, 0) + 1
            
            # Format practice history
            practice_history = []
            for sub in submissions:
                practice_history.append({
                    'submission_id': sub.id,
                    'problem_id': sub.problem.id,
                    'problem_title': sub.problem.title,
                    'problem_difficulty': sub.problem.difficulty,
                    'result': sub.result,
                    'result_text': self.get_result_text(sub.result),
                    'language': sub.language,
                    'create_time': sub.create_time.isoformat(),
                })
            
            statistics = {
                "total_problems_solved": total_problems_solved,
                "recent_submissions": recent_total,
                "recent_accepted": recent_accepted,
                "recent_acceptance_rate": round(recent_acceptance_rate, 2),
                "difficulty_distribution": difficulty_dist,
                "analysis_period_days": days
            }
            
            return self.success({
                "practice_history": practice_history,
                "statistics": statistics
            })
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in practice history: {str(e)}")
            return self.error(f"An error occurred: {str(e)}")
    
    def get_result_text(self, result):
        """Convert result code to human-readable text"""
        result_map = {
            JudgeStatus.COMPILE_ERROR: "Compile Error",
            JudgeStatus.WRONG_ANSWER: "Wrong Answer",
            JudgeStatus.ACCEPTED: "Accepted",
            JudgeStatus.CPU_TIME_LIMIT_EXCEEDED: "Time Limit Exceeded",
            JudgeStatus.REAL_TIME_LIMIT_EXCEEDED: "Time Limit Exceeded",
            JudgeStatus.MEMORY_LIMIT_EXCEEDED: "Memory Limit Exceeded",
            JudgeStatus.RUNTIME_ERROR: "Runtime Error",
            JudgeStatus.SYSTEM_ERROR: "System Error",
            JudgeStatus.PENDING: "Pending",
            JudgeStatus.JUDGING: "Judging",
            JudgeStatus.PARTIALLY_ACCEPTED: "Partially Accepted"
        }
        return result_map.get(result, "Unknown")