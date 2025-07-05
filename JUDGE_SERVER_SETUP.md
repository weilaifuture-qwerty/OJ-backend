# OnlineJudge - Judge Server Setup Guide

## Prerequisites

1. **Backend Server Running**
   ```bash
   cd /Users/weilai/Desktop/Fufu_website/website10/OJ/OnlineJudge
   python manage.py runserver
   ```

2. **Redis Server Running**
   ```bash
   # macOS
   brew services start redis
   
   # Or manually
   redis-server
   ```

3. **Judge Server Running**
   The judge server needs to be running separately. It's typically a Docker container.

## Setting Up Judge Server

### Option 1: Using Docker (Recommended)

1. **Pull the Judge Server Image**
   ```bash
   docker pull registry.cn-hangzhou.aliyuncs.com/onlinejudge/judge_server
   ```

2. **Run Judge Server**
   ```bash
   docker run -it -d \
     --name judge-server \
     -p 12358:8080 \
     --cap-add=SYS_PTRACE \
     --restart=always \
     registry.cn-hangzhou.aliyuncs.com/onlinejudge/judge_server
   ```

3. **Get Judge Server Token**
   ```bash
   docker exec judge-server cat /judger/token.txt
   ```

### Option 2: Using Docker Compose

1. **Create docker-compose.yml**
   ```yaml
   version: "3"
   services:
     oj-redis:
       image: redis:6.0-alpine
       volumes:
         - ./data/redis:/data
       ports:
         - "6380:6379"
     
     judge-server:
       image: registry.cn-hangzhou.aliyuncs.com/onlinejudge/judge_server
       cap_add:
         - SYS_PTRACE
       ports:
         - "12358:8080"
       volumes:
         - ./data/judge_server:/judger
   ```

2. **Start Services**
   ```bash
   docker-compose up -d
   ```

## Configure Backend

1. **Add Judge Server in Admin Panel**
   - Login as admin
   - Go to http://localhost:8000/admin/
   - Navigate to "Judge Servers"
   - Add new judge server with:
     - Service URL: http://localhost:12358
     - Token: (from the judge server)

2. **Via Django Shell**
   ```python
   python manage.py shell
   
   from conf.models import JudgeServer
   from options.options import SysOptions
   
   # Set judge server token
   token = "YOUR_JUDGE_SERVER_TOKEN"  # Get from docker exec command
   SysOptions.judge_server_token = token
   
   # Register judge server (if not auto-registered)
   JudgeServer.objects.create(
       hostname="local-judge",
       ip="127.0.0.1",
       service_url="http://localhost:12358",
       judger_version="2.0.0",
       cpu_core=4,
       memory_usage=0,
       cpu_usage=0,
       last_heartbeat=timezone.now()
   )
   ```

## Testing Judge Server

1. **Check Connection**
   ```bash
   python check_judge_server.py
   ```

2. **Test Submission**
   ```bash
   python test_judge_submission.py
   ```

3. **Manual Test**
   - Login to OnlineJudge
   - Go to Problems
   - Select a problem (e.g., A+B Problem)
   - Submit a solution
   - Check if it gets judged

## Common Issues

### 1. Judge Server Not Connecting
- Check if Docker container is running: `docker ps`
- Check logs: `docker logs judge-server`
- Verify port 12358 is accessible
- Check firewall settings

### 2. Submissions Stay Pending
- Check Redis is running
- Check Celery workers (if used)
- Check judge server logs
- Verify token matches between backend and judge server

### 3. Network Issues
- Ensure backend can reach judge server
- Try using host.docker.internal instead of localhost if backend is in Docker
- Check CORS/CSRF settings

### 4. Permission Issues
- Judge server needs SYS_PTRACE capability
- Check Docker permissions
- Verify file permissions in mounted volumes

## Debug Commands

```bash
# Check judge server health
curl http://localhost:12358/

# Check backend API
curl http://localhost:8000/api/

# View judge server logs
docker logs -f judge-server

# Check Redis
redis-cli ping

# Django shell - check judge servers
python manage.py shell
>>> from conf.models import JudgeServer
>>> JudgeServer.objects.all()
>>> from options.options import SysOptions
>>> SysOptions.judge_server_token
```

## API Endpoints to Test

1. **Get Languages**
   ```
   GET http://localhost:8000/api/languages/
   ```

2. **Submit Code**
   ```
   POST http://localhost:8000/api/submission/
   {
     "problem_id": "1",
     "language": "Python3",
     "code": "a, b = map(int, input().split())\\nprint(a + b)"
   }
   ```

3. **Check Submission**
   ```
   GET http://localhost:8000/api/submission?id=SUBMISSION_ID
   ```

## Next Steps

After judge server is working:
1. Add test cases to problems
2. Configure time/memory limits
3. Set up multiple judge servers for load balancing
4. Configure special judge for custom validation