# Debugging Empty Dropdown Issue

The dropdown is opening but showing no data. Here are the potential causes and solutions:

## 1. Authentication Issue
The APIs require admin authentication. Make sure:
- You're logged in as an admin user
- The session cookie is being sent with requests

## 2. No Student Data
Check if there are any students in the database:
```sql
SELECT COUNT(*) FROM user WHERE admin_type = 'Regular User';
SELECT COUNT(*) FROM user_profile WHERE student_group IS NOT NULL;
```

## 3. API Response Format
The frontend might be expecting a different response format. Check the browser's Network tab to see:
- What URL is being called
- What the response looks like
- Any error messages

## 4. Quick Fix - Add Test Data

Run this in Django shell (`python manage.py shell`):

```python
from account.models import User, UserProfile, AdminType

# Check existing students
students = User.objects.filter(admin_type=AdminType.REGULAR_USER)
print(f"Found {students.count()} students")

# Add groups to existing students
groups = ["Class A", "Class B", "Class C"]
for i, student in enumerate(students[:10]):
    profile, created = UserProfile.objects.get_or_create(user=student)
    profile.student_group = groups[i % len(groups)]
    profile.save()
    print(f"Updated {student.username} with group {profile.student_group}")

# Verify groups exist
from django.db.models import Count
group_counts = UserProfile.objects.filter(
    user__admin_type=AdminType.REGULAR_USER
).exclude(student_group__isnull=True).values('student_group').annotate(count=Count('id'))
for g in group_counts:
    print(f"Group '{g['student_group']}': {g['count']} students")
```

## 5. Check API Endpoints Directly

Open these URLs in your browser (while logged in as admin):
- http://localhost:8080/api/available_groups
- http://localhost:8080/api/available_students
- http://localhost:8080/api/students_by_group
- http://localhost:8080/api/users?type=student

## 6. Frontend Component Issue

Make sure the frontend is calling the correct endpoints. The dropdown component should:

1. Call `/api/available_groups` to get the list of groups
2. Call `/api/available_students` or `/api/users?type=student` to get students

## 7. Check Browser Console

Look for any JavaScript errors in the browser console that might prevent the dropdown from populating.

## 8. Verify API Permission

The issue might be that the logged-in user doesn't have admin privileges. Check the user's admin_type:

```python
# In Django shell
from account.models import User
user = User.objects.get(username='your_username')
print(f"User {user.username} has admin_type: {user.admin_type}")
# Should be 'Admin' or 'Super Admin'
```

## Next Steps

1. Check the Network tab in browser DevTools when opening the dropdown
2. Look at the actual API response
3. Share the API response so we can see what's being returned
4. Check if there are any JavaScript errors in the console