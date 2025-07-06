# Run Migrations for New Features

To apply the new models and fields added for the homework and user features, run:

```bash
# Activate virtual environment
source oj_env/bin/activate

# Create migrations
python manage.py makemigrations account
python manage.py makemigrations homework

# Apply migrations
python manage.py migrate
```

## New Models Added:

### In account app:
- `UserStreak` - Track daily check-ins and streaks
- `DailyProblemSuggestion` - Daily problem recommendations
- `ProblemSuggestion` - AI-powered problem suggestions

### Updated fields:
- `UserStreak.total_problems_solved` - Track total solved
- `UserStreak.check_in_days` - JSON field for check-in history

## Troubleshooting:

If you get migration conflicts:
```bash
# Show current migrations
python manage.py showmigrations

# If needed, fake the conflicting migration
python manage.py migrate account 0017 --fake
python manage.py migrate account
```

## After migrations:

The server should start without import errors:
```bash
python manage.py runserver
```