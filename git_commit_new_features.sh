#!/bin/bash

echo "=== Git Commit and Push Script ==="
echo

# Add all changes
echo "1. Staging all changes..."
git add -A

# Show summary of changes
echo -e "\n2. Summary of changes:"
git status --short | wc -l | xargs echo "Total files changed:"
echo "Key changes:"
git status --short | grep -E "(models|views|serializers|signals)" | head -10

# Create commit
echo -e "\n3. Creating commit..."
git commit -m "Add daily check-in, AI suggestions, and enhanced homework APIs

- Implemented daily problem suggestion API with AI reasoning
- Added user streak tracking and daily check-in functionality  
- Created AI-powered problem recommendations with match scoring
- Enhanced homework APIs to use real submission data
- Added homework comments system with threading
- Implemented batch problem status check API
- Added automatic homework status updates via signals
- Fixed timezone handling for daily check-ins
- Updated homework list/detail to show real-time progress

New models:
- UserStreak, DailyProblemSuggestion, ProblemSuggestion
- Enhanced HomeworkComment with replies

New endpoints:
- GET /api/problem/daily-suggestion/
- GET /api/user/streak/
- POST /api/user/daily-check-in/
- GET /api/problem/suggestions/
- GET/POST/DELETE /api/homework/{id}/comments/
- GET /api/homework/{id}/problem-status/
- POST /api/problems/check-status/

Co-authored-by: Claude <assistant@anthropic.com>"

# Show the last commit
echo -e "\n4. Last commit:"
git log --oneline -1

# Push to GitHub
echo -e "\n5. Pushing to GitHub..."
git push origin main

echo -e "\n✅ Done!"