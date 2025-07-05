# Immediate Fix for Login Error

The error is happening because we added a new field `student_group` to the UserProfile model but the database doesn't have this column yet.

## Option 1: Run Migrations (Recommended)

```bash
cd /Users/weilai/Desktop/Fufu_website/website10/OJ/OnlineJudge
source oj_env/bin/activate

# Install missing package first
pip install django-dramatiq redis

# Create and run migrations
python manage.py makemigrations account
python manage.py migrate

# Restart server
python manage.py runserver
```

## Option 2: Quick Database Fix

If you have database access, run this SQL command:

```sql
ALTER TABLE user_profile ADD COLUMN student_group VARCHAR(100) DEFAULT NULL;
```

## Option 3: Temporary Code Fix

If you can't run migrations right now, temporarily comment out the field:

1. Open `/Users/weilai/Desktop/Fufu_website/website10/OJ/OnlineJudge/account/models.py`
2. Find line 108: `student_group = models.CharField(max_length=100, blank=True, null=True)`
3. Comment it out: `# student_group = models.CharField(max_length=100, blank=True, null=True)`
4. Save and restart the server

## Option 4: Fix the Serializer (Quick Patch)

Edit `/Users/weilai/Desktop/Fufu_website/website10/OJ/OnlineJudge/account/serializers.py`:

Change line 77 from:
```python
fields = "__all__"
```

To:
```python
fields = ["id", "user", "acm_problems_status", "oi_problems_status", 
          "real_name", "avatar", "blog", "mood", "github", "school", 
          "major", "language", "accepted_number", "total_score", 
          "submission_number", "status", "status_message", "mood_emoji", 
          "mood_clear_at", "status_color"]
```

This explicitly lists fields without the new `student_group` field.

## Best Solution

Run Option 1 (migrations) as it properly updates the database schema. The other options are temporary workarounds.

After fixing, you should be able to login successfully!