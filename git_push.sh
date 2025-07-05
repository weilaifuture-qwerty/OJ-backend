#!/bin/bash

echo "=== Git Push Script ==="
echo

# Add all changes
echo "1. Adding all changes..."
git add -A

# Show what will be committed
echo -e "\n2. Files to be committed:"
git status --short | head -20
if [ $(git status --short | wc -l) -gt 20 ]; then
    echo "... and $(( $(git status --short | wc -l) - 20 )) more files"
fi

# Commit with message
echo -e "\n3. Creating commit..."
git commit -m "$(cat <<'EOF'
Implement homework backend endpoints and fix judge server setup

- Added all homework management REST endpoints from HOMEWORK_BACKEND_ENDPOINTS.md
- Fixed navbar layout width issues (increased to 1600px)
- Removed debug panels from frontend
- Created A+B problem with test cases
- Configured judge server with correct token
- Created comprehensive test scripts for judge system
- Fixed authentication issues in submission tests
- Documented macOS Docker limitation for judge server

Co-authored-by: Claude <claude@anthropic.com>
EOF
)"

# Push to remote
echo -e "\n4. Pushing to GitHub..."
git push origin main

echo -e "\n✅ Done! Changes pushed to GitHub."