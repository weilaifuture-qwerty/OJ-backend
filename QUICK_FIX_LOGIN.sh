#!/bin/bash

# Quick fix for login error due to missing student_group field

echo "Fixing login error..."

cd /Users/weilai/Desktop/Fufu_website/website10/OJ/OnlineJudge

# Activate virtual environment
source oj_env/bin/activate

# Try to create and run migrations
echo "Creating migrations..."
python manage.py makemigrations account

echo "Running migrations..."
python manage.py migrate

echo "Done! Try logging in again."
echo ""
echo "If this doesn't work, run these SQL commands directly in your database:"
echo "ALTER TABLE user_profile ADD COLUMN student_group VARCHAR(100) DEFAULT NULL;"
echo ""
echo "Or temporarily comment out the student_group field in account/models.py line 108"