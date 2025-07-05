# Start Both Servers

You need to run BOTH the frontend and backend servers:

## 1. Start Django Backend Server (Terminal 1)

```bash
cd /Users/weilai/Desktop/Fufu_website/website10/OJ/OnlineJudge
source oj_env/bin/activate
python manage.py runserver
```

The Django server should start on http://localhost:8000

## 2. Keep Frontend Server Running (Terminal 2)

The frontend Vite server is already running (that's why you see the Vite errors).
It's running on http://localhost:8080

## Why This Happens

- Frontend (Vue/Vite) runs on port 8080
- Backend (Django) runs on port 8000
- Frontend makes API calls to backend
- If backend is not running, you get ECONNREFUSED errors

## Quick Check

After starting Django server, you should see:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

## If Django Server Won't Start

If you get errors when starting Django:

1. Check for syntax errors:
   ```bash
   python manage.py check
   ```

2. Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. If still having issues:
   ```bash
   python diagnose_server.py
   ```

## Success Indicators

When both servers are running correctly:
- No more ECONNREFUSED errors
- API calls work (no 500 errors)
- Dropdown shows groups
- Can create homework