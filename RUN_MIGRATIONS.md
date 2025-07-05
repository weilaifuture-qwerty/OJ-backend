# Run Migrations to Fix the Issues

The server errors are happening because of missing database migrations. Run these commands:

```bash
cd /Users/weilai/Desktop/Fufu_website/website10/OJ/OnlineJudge
source oj_env/bin/activate

# Create migrations for the homework app
python manage.py makemigrations homework

# Apply the migrations
python manage.py migrate

# Restart the server
python manage.py runserver
```

## What This Fixes

1. **Adds the missing `related_name='problems'`** to HomeworkProblem model
2. **Ensures all model relationships are properly set up**

## After Running Migrations

1. The dropdown should show all 5 groups (Class A, B, C, Advanced, Beginners)
2. Creating homework should work without server errors
3. The homework list should load without errors

## Verify Everything Works

After migrations, run:
```bash
python verify_system.py
```

This will show you the complete system status and verify all components are working.

## If Still Having Issues

Check the Django console for any error messages when:
1. Loading the homework page
2. Creating new homework

The error handling I added will show the exact problem in the console.