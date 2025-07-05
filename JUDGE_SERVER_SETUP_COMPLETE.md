# Judge Server Setup Complete Guide

## Current Status
✅ Django server is running
✅ Root user created (username: root, password: rootroot)
✅ A+B Problem created (ID: 5, display ID: 1)
✅ Judge server container is running (but unhealthy)
✅ Submission API is working
⚠️ Dramatiq worker needs to be started for judge tasks

## To Complete Setup

### 1. Start Dramatiq Worker (Required for judging)
In a new terminal:
```bash
cd /Users/weilai/Desktop/Fufu_website/website10/OJ/OnlineJudge
source oj_env/bin/activate
python manage.py rundramatiq
```

### 2. Configure Judge Server Token
The judge server is using token "YOUR_TOKEN_HERE". Configure it:
```bash
source oj_env/bin/activate
python manage.py shell
>>> from options.options import SysOptions
>>> SysOptions.judge_server_token = "YOUR_TOKEN_HERE"
>>> from conf.models import JudgeServer
>>> JudgeServer.objects.create(
...     hostname="judge-server",
...     ip="http://localhost:12358",
...     judger_version="2.0.0",
...     cpu_core=4,
...     memory_usage=0,
...     cpu_usage=0,
...     last_heartbeat=timezone.now(),
...     create_time=timezone.now(),
...     task_number=0,
...     service_url="http://localhost:12358",
...     is_disabled=False
... )
>>> exit()
```

### 3. Test Submission
After starting Dramatiq:
```bash
python test_judge_final.py
```

## Quick Test Commands

### Check if everything is running:
```bash
# Check Django
curl http://localhost:8000/api/

# Check Judge Server
curl http://localhost:12358/

# Check Redis
redis-cli -p 6380 ping

# Check Docker
docker ps | grep judge
```

### Submit via API:
```bash
# Login and submit
python test_judge_final.py
```

### Submit via Web:
1. Go to http://localhost:8000
2. Login as root/rootroot
3. Click "Problems"
4. Click "A+B Problem"
5. Submit this code:
```python
a, b = map(int, input().split())
print(a + b)
```

## Troubleshooting

### If submissions stay "Pending":
- Make sure Dramatiq is running: `python manage.py rundramatiq`
- Check Redis is running: `redis-cli -p 6380 ping`
- Check judge server logs: `docker logs judgeserver-judge_server-1`

### If you get "Compile Error":
- The judge server might not be configured correctly
- Check test case files exist in `data/test_case/ab_problem_test/`
- Verify judge server token matches

### If judge server is unhealthy:
- Restart it: `docker restart judgeserver-judge_server-1`
- Check configuration in admin panel

## Files Created
- `/test_judge_final.py` - Comprehensive test script
- `/create_root_user.py` - Creates admin user
- `/create_ab_problem_simple.py` - Creates A+B problem
- `/start_dramatiq.sh` - Starts task worker

## Next Steps
1. Start Dramatiq worker
2. Run test_judge_final.py
3. If successful, the judge server is fully operational!