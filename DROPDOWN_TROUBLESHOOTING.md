# Dropdown Not Showing Data - Troubleshooting Guide

## Problem
The dropdown is opening (`[handleDropdownOpen] Dropdown opened: true`) but no data is displayed.

## Quick Diagnosis

1. **Open this URL in your browser** (while Django server is running):
   ```
   http://localhost:8080/api/debug_groups
   ```
   This will show you:
   - Total number of students
   - How many have groups assigned
   - List of available groups
   - Sample student data

2. **Check these API endpoints** (must be logged in as admin):
   - http://localhost:8080/api/available_groups
   - http://localhost:8080/api/available_students
   - http://localhost:8080/api/users?type=student

## Common Issues and Solutions

### 1. No Students in Database
If `total_students` is 0 in the debug endpoint, create test students:

```bash
cd /Users/weilai/Desktop/Fufu_website/website10/OJ/OnlineJudge
source oj_env/bin/activate
python manage.py shell
```

Then run:
```python
from account.models import User, UserProfile, AdminType

# Create test students with groups
groups = ["Class A", "Class B", "Class C", "Advanced", "Beginners"]
for i in range(1, 11):
    user = User.objects.create(
        username=f'teststudent{i}',
        email=f'teststudent{i}@example.com',
        admin_type=AdminType.REGULAR_USER
    )
    user.set_password('password123')
    user.save()
    
    UserProfile.objects.create(
        user=user,
        real_name=f'Test Student {i}',
        student_group=groups[(i-1) % len(groups)]
    )

print("Created 10 test students with groups")
```

### 2. Students Exist but No Groups
If students exist but `students_with_groups` is 0:

```python
from account.models import User, UserProfile, AdminType

# Add groups to existing students
students = User.objects.filter(admin_type=AdminType.REGULAR_USER)[:10]
groups = ["Class A", "Class B", "Class C"]

for i, student in enumerate(students):
    profile, created = UserProfile.objects.get_or_create(user=student)
    profile.student_group = groups[i % len(groups)]
    profile.save()

print(f"Updated {len(students)} students with groups")
```

### 3. Authentication Issue
The APIs require admin authentication. Check if you're logged in as admin:

```python
# In Django shell
from account.models import User
admin = User.objects.get(username='your_admin_username')
print(f"Admin type: {admin.admin_type}")
# Should be 'Admin' or 'Super Admin'
```

### 4. Frontend Integration Issue

Check the browser's Developer Tools:

1. **Network Tab**: When dropdown opens, look for API calls to:
   - `/api/available_groups`
   - `/api/available_students`
   
2. **Console Tab**: Check for JavaScript errors

3. **Response Format**: The API should return:
   ```json
   {
     "error": null,
     "data": {
       "groups": ["Class A", "Class B", "Class C"],
       "count": 3
     }
   }
   ```

### 5. Quick Test in Browser Console

Run this in the browser console to test the API:

```javascript
// Test available groups
fetch('/api/available_groups', { credentials: 'include' })
  .then(r => r.json())
  .then(data => console.log('Groups:', data));

// Test available students
fetch('/api/available_students', { credentials: 'include' })
  .then(r => r.json())
  .then(data => console.log('Students:', data));
```

## Fixed Issues

1. ✅ Fixed admin type comparison in `AvailableStudentsAPI` (was using strings instead of constants)
2. ✅ Added all necessary API endpoints
3. ✅ Created debug endpoint for troubleshooting

## Next Steps

1. Visit http://localhost:8080/api/debug_groups to see current data status
2. If no students/groups exist, use the shell commands above to create test data
3. Check browser console for any JavaScript errors
4. Verify the frontend component is calling the correct endpoints

The backend APIs are ready and working. The issue is likely:
- No data in database
- Authentication/permission issue
- Frontend not calling the correct endpoints