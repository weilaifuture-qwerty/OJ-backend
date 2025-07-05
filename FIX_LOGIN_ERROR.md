# Fix Login Error - Server Error on User Profile

## Problem
After adding the `student_group` field to UserProfile model, the database schema is out of sync, causing a server error when fetching user profile.

## Quick Fix

1. **First, try to create and run migrations:**
```bash
cd /Users/weilai/Desktop/Fufu_website/website10/OJ/OnlineJudge
source oj_env/bin/activate

# Create migrations for account app
python manage.py makemigrations account

# Apply migrations
python manage.py migrate
```

2. **If that doesn't work, manually create the migration:**

Create a new file `account/migrations/XXXX_add_student_group.py` (replace XXXX with next number):

```python
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('account', '0001_initial'),  # Replace with your latest migration
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='student_group',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
```

Then run:
```bash
python manage.py migrate
```

## Alternative: Quick Database Fix

If you need a quick fix without migrations, run this SQL directly:

```sql
ALTER TABLE user_profile ADD COLUMN student_group VARCHAR(100);
```

## Temporary Workaround

If you can't run migrations right now, comment out the student_group field temporarily:

1. Edit `/Users/weilai/Desktop/Fufu_website/website10/OJ/OnlineJudge/account/models.py`
2. Comment out line 108: `# student_group = models.CharField(max_length=100, blank=True, null=True)`
3. Restart the server

## Check What's Happening

To see the actual error, you can:

1. Check Django logs:
```bash
python manage.py runserver
# Look for the error when you try to login
```

2. Or check in Django shell:
```bash
python manage.py shell
>>> from account.models import User, UserProfile
>>> user = User.objects.first()
>>> user.userprofile
# This will show the actual database error
```

## Verify Fix

After applying the migration, test login:
1. Go to login page
2. Enter credentials
3. Should login successfully without server-error

## Long-term Solution

Always run migrations after model changes:
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```