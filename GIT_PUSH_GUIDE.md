# Git Push Guide for OJ Backend

## Repository Information
- **Repository URL**: https://github.com/weilaifuture-qwerty/OJ-backend
- **Local Path**: /Users/weilai/Desktop/Fufu_website/website10/OJ/OnlineJudge

## Quick Push Commands

### Option 1: Push All Changes (Recommended)
```bash
# Navigate to project directory
cd /Users/weilai/Desktop/Fufu_website/website10/OJ/OnlineJudge

# Check current status
git status

# Add all changes
git add .

# Commit with a descriptive message
git commit -m "Add daily check-in, AI suggestions, homework system, avatar upload, and user status features"

# Push to GitHub
git push origin main
```

### Option 2: Selective Push
```bash
# Add specific files
git add account/models.py
git add account/views/oj.py
git add account/serializers.py
git add account/urls/oj.py
git add homework/
git add account/views/ai_suggestions.py
git add account/management/

# Commit
git commit -m "Add new features: check-in, AI suggestions, homework, status system"

# Push
git push origin main
```

## Features Added in This Session

### 1. Daily Check-in System
- Streak tracking
- Daily check-in API
- Auto streak calculation

### 2. AI-Powered Problem Suggestions
- Smart problem recommendations
- User practice profile tracking
- Skill-based matching

### 3. Homework Assignment System
- Admin can assign homework
- Student homework tracking
- Grading and feedback

### 4. Avatar System Enhancement
- Image upload with processing
- Avatar deletion
- Absolute URL support

### 5. User Status System
- Activity status (practicing, learning, etc.)
- Mood messages with emojis
- Auto-expiration support

## Important Files to Include

### Must Include:
- `account/models.py` - New models for all features
- `account/views/oj.py` - API views
- `account/serializers.py` - Updated serializers
- `account/urls/oj.py` - New URL patterns
- `account/views/ai_suggestions.py` - AI suggestion logic
- `account/management/` - Management commands
- `homework/` - Entire homework app
- `oj/urls.py` - Avatar serving configuration
- `utils/api/api.py` - Base API updates
- `utils/api/_serializers.py` - Username serializer update

### Don't Include:
- `oj_env/` - Virtual environment
- `data/` - Local data files
- `*.pyc` - Compiled Python files
- `__pycache__/` - Python cache
- Database files

## Create .gitignore (if needed)
```bash
# Create .gitignore file
cat > .gitignore << EOF
# Python
*.pyc
__pycache__/
*.py[cod]
*$py.class

# Virtual Environment
oj_env/
venv/
env/

# Data and Media
data/
media/
public/

# Database
*.sqlite3
*.db

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Environment variables
.env
.env.local

# Test files
test_*.py
*_test.py
EOF
```

## Authentication Options

### Option 1: HTTPS with Token (Recommended)
1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token with 'repo' scope
3. Use token as password when pushing:
   ```bash
   git push https://github.com/weilaifuture-qwerty/OJ-backend.git main
   # Username: your-github-username
   # Password: your-personal-access-token
   ```

### Option 2: SSH Key
```bash
# Check if you have SSH key
ls ~/.ssh/id_rsa.pub

# If not, generate one
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Copy SSH key
cat ~/.ssh/id_rsa.pub

# Add to GitHub: Settings → SSH and GPG keys → New SSH key
```

## Troubleshooting

### If push is rejected:
```bash
# Pull latest changes first
git pull origin main --rebase

# Then push
git push origin main
```

### If you have merge conflicts:
```bash
# See conflicted files
git status

# Edit files to resolve conflicts
# Then add and commit
git add .
git commit -m "Resolve merge conflicts"
git push origin main
```

### To see what will be pushed:
```bash
git log origin/main..HEAD --oneline
```

## Complete Push Workflow

```bash
# 1. Navigate to project
cd /Users/weilai/Desktop/Fufu_website/website10/OJ/OnlineJudge

# 2. Check status
git status

# 3. Add all changes
git add .

# 4. Commit with detailed message
git commit -m "Major update: Add daily check-in with streak tracking, AI-powered problem suggestions, homework assignment system, enhanced avatar upload, and user status system with mood support"

# 5. Push to GitHub
git push origin main

# 6. Verify on GitHub
# Visit: https://github.com/weilaifuture-qwerty/OJ-backend
```

## After Pushing

1. Check the repository on GitHub to ensure all files are uploaded
2. Update README.md with new features (if needed)
3. Create releases/tags for major versions
4. Document any new environment variables or setup requirements

Good luck with your push! 🚀