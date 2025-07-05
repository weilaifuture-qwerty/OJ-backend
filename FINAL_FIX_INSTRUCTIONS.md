# Final Fix Instructions

## What I've Done

1. **Added error handling** to the problematic views to see the actual errors in Django console
2. **Fixed the prefetch_related issue** in AdminHomeworkListAPI
3. **Fixed super admin support** in AdminCreateHomeworkAPI
4. **Created debug endpoints** to help troubleshoot

## Steps to Fix Everything

### 1. Add Student Groups (Fix Empty Dropdown)

```bash
cd /Users/weilai/Desktop/Fufu_website/website10/OJ/OnlineJudge
source oj_env/bin/activate
python add_student_groups.py
```

### 2. Check Debug Information

Visit this URL while logged in as admin:
```
http://localhost:8080/api/homework_debug
```

This will show you:
- Current user info
- Total counts of students, problems, homework
- Group information
- Test query results

### 3. Watch Django Console

When you try to create homework or load the homework list, watch the Django console for error messages. The error handling I added will print the full stack trace.

### 4. Common Issues

#### If still getting "server-error":
1. Check Django console for the actual error
2. Make sure you have at least one Problem in the database
3. Make sure the user is properly authenticated

#### If dropdown still empty after running script:
1. Refresh the page completely (Ctrl+F5)
2. Check console to confirm groups were added:
   ```
   api.js:461 [AJAX] Success - data: {groups: Array(5), count: 5}
   ```

### 5. Test Direct API Calls

You can test the APIs directly in browser:
- http://localhost:8080/api/homework_debug (debug info)
- http://localhost:8080/api/available_groups (should show groups after script)
- http://localhost:8080/api/available_students (should show 5 students)

## What to Look For

When you run the server and try to create homework, the Django console will now show:
1. The actual error causing "server-error"
2. Full stack trace
3. Which line is failing

Share the Django console error output and I can help fix the specific issue.

## Quick Test

After running the add_student_groups.py script, the console should show:
```
[loadGroups] Groups data: ["Class A", "Class B", "Class C", "Advanced", "Beginners"]
```

Instead of:
```
[loadGroups] Groups data: []
```