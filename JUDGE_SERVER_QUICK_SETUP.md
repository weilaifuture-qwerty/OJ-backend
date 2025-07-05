# Judge Server Quick Setup Guide

## Current Status ✓
- ✅ Judge server Docker container is running
- ✅ Judge server is accessible on port 12358
- ✅ Redis is running (on port 6380)
- ✅ Default token identified: `YOUR_TOKEN_HERE`
- ⚠️ Token needs to be configured in Django

## Steps to Complete Setup

### 1. Configure Judge Server Token

Run these commands:
```bash
# Start Django server first
python manage.py runserver

# In another terminal, configure the judge server
python manage.py setup_judge_server

# Or manually in Django shell:
python manage.py shell
>>> from options.options import SysOptions
>>> SysOptions.judge_server_token = "YOUR_TOKEN_HERE"
>>> exit()
```

### 2. Create A+B Problem
```bash
python manage.py create_ab_problem
```

### 3. Test the Setup
```bash
# Make sure Django server is running
python manage.py runserver

# Run the test
python test_judge_submission.py
```

## Manual Testing via Web Interface

1. Go to http://localhost:8000
2. Login as `root` / `rootroot`
3. Go to Problems section
4. Click on "A+B Problem"
5. Submit this solution:
   ```python
   a, b = map(int, input().split())
   print(a + b)
   ```

## Expected Output

When you run `test_judge_submission.py`, you should see:
```
✓ Login successful
✓ Judge server connected
✓ Submission created
✓ Result: Accepted (0)
```

## Troubleshooting

### If submission stays "Pending":
1. Check Celery is running (if used)
2. Check Redis connection
3. Check judge server logs: `docker logs judgeserver-judge_server-1`

### If you get "Wrong Answer":
- Make sure test cases are created in `data/test_case/ab_problem_test/`
- Check output format (should have newline at end)

### If you get connection errors:
- Ensure Django server is running: `python manage.py runserver`
- Check Redis is on port 6380: `redis-cli -p 6380 ping`
- Verify judge server: `curl http://localhost:12358/`

## Quick Test Command

After setup, run this one-liner to test:
```bash
curl -X POST http://localhost:8000/api/submission/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -d '{"problem_id": "1", "language": "Python3", "code": "a, b = map(int, input().split())\\nprint(a + b)"}'
```

## Success Indicators

- Judge server status shows "normal" in admin panel
- Submissions get judged within a few seconds
- A+B problem shows AC (Accepted) status

## Next Steps

Once working:
1. Add more problems
2. Create contests
3. Configure multiple judge servers
4. Set up problem tags and categories