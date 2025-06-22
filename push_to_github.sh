#!/bin/bash
# Script to push OnlineJudge backend to GitHub

echo "===== Git Push Helper for OJ Backend ====="
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not in a git repository!"
    exit 1
fi

# Show current status
echo "1. Current Git Status:"
echo "====================="
git status
echo ""

# Show current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"
echo ""

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "2. You have uncommitted changes. Let's commit them:"
    echo "==================================================="
    
    # Add all changes
    echo "Adding all changes..."
    git add .
    
    # Show what will be committed
    echo ""
    echo "Files to be committed:"
    git status --short
    
    # Commit with a message
    echo ""
    read -p "Enter commit message: " commit_message
    git commit -m "$commit_message"
    echo "Changes committed!"
else
    echo "2. No uncommitted changes found."
fi

echo ""
echo "3. Pushing to GitHub:"
echo "===================="

# Push to remote
echo "Pushing to origin/$CURRENT_BRANCH..."
git push origin $CURRENT_BRANCH

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo "🔗 Repository: https://github.com/weilaifuture-qwerty/OJ-backend"
else
    echo ""
    echo "❌ Push failed. Common issues:"
    echo "   - Authentication required (enter GitHub username/password or use token)"
    echo "   - No internet connection"
    echo "   - Branch protection rules"
    echo ""
    echo "Try running: git push -u origin $CURRENT_BRANCH"
fi