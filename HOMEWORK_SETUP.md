# Homework System Setup Instructions

## Quick Fix for django-dramatiq Error

```bash
cd /Users/weilai/Desktop/Fufu_website/website10/OJ/OnlineJudge
source oj_env/bin/activate
pip install django-dramatiq redis
```

## Create and Run Migrations

```bash
# Make migrations for the homework app
python manage.py makemigrations homework

# Apply all migrations
python manage.py migrate
```

## Test the Endpoints

1. **Run the test script to verify endpoints:**
```bash
python manage.py shell < test_homework_endpoints.py
```

2. **Start the Django server:**
```bash
python manage.py runserver
```

3. **Test the debug endpoint:**
Visit: http://localhost:8000/api/homework_debug/

## Available Endpoints

### Student Endpoints:
- GET `/api/student_homework` - Get student's homework list
- GET `/api/student_homework_detail?id=<homework_id>` - Get homework detail
- GET `/api/homework_progress` - Get progress counts
- POST `/api/submit_homework_problem` - Submit problem solution
- GET `/api/homework_comments?homework_id=<id>` - Get comments
- POST `/api/homework_comments` - Create comment
- DELETE `/api/homework_comments?id=<comment_id>` - Delete comment

### Admin Endpoints:
- GET `/api/admin_homework_list` - Get admin's homework list
- POST `/api/admin_create_homework` - Create new homework
- DELETE `/api/admin_delete_homework?id=<homework_id>` - Delete homework
- GET `/api/available_students` - Get available students

### Additional Admin Endpoints (under /api/admin/):
- GET `/api/admin/admin_student_relation` - Manage student assignments
- GET `/api/admin/homework_detail?id=<homework_id>` - Get detailed homework info
- POST `/api/admin/grade_homework` - Grade student homework
- GET `/api/admin/homework_statistics` - Get homework statistics

## Troubleshooting

If you still get 404 errors:

1. **Check if the homework app is in INSTALLED_APPS:**
```python
# In oj/settings.py, make sure 'homework' is listed:
INSTALLED_APPS = [
    # ... other apps
    'homework',
]
```

2. **Verify URL includes in main urls.py:**
```python
# In oj/urls.py, these should exist:
re_path(r"^api/", include("homework.urls.oj")),
re_path(r"^api/admin/", include("homework.urls.admin")),
```

3. **Check for import errors:**
```bash
python manage.py check
```

## Frontend Integration

The frontend expects these exact URLs, so the backend now provides:
- `/api/admin_homework_list` (not `/api/admin/admin_homework_list`)
- `/api/available_students` (not `/api/admin/available_students`)

This is achieved by including some admin views in the regular `/api/` namespace rather than `/api/admin/`.