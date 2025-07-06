# Frontend Date Handling Fix for Daily Check-in

## The Problem

The backend stores dates in UTC, but the frontend needs to handle them in the user's local timezone. When a user in PDT (UTC-7) checks in at 5:35 PM on July 5th, it's already July 6th in UTC.

## Frontend Fixes Needed

### 1. Update `checkedInToday` computed property in DailyCheckIn.vue

```javascript
checkedInToday() {
  if (!this.streakData.last_check_in) {
    return false;
  }
  
  // Get today's date in local timezone
  const today = moment().format('YYYY-MM-DD');
  
  // Check if today is in the check_in_days array
  return this.streakData.check_in_days && 
         this.streakData.check_in_days.includes(today);
}
```

### 2. Update calendar day checking logic

```javascript
isCheckedIn(day) {
  if (!this.streakData.check_in_days) return false;
  
  // Format the calendar day to match check_in_days format
  const dayStr = moment(day).format('YYYY-MM-DD');
  return this.streakData.check_in_days.includes(dayStr);
}
```

### 3. Backend Fix - Store dates in user's timezone

Update the backend to store check-in dates in the user's local date, not UTC date:

In `account/models.py`, update the `UserStreak.check_in()` method:

```python
def check_in(self, user_timezone=None):
    """Record a daily check-in"""
    from django.utils import timezone
    import pytz
    
    # Get current time
    now = timezone.now()
    
    # If user timezone is provided, convert to that timezone
    if user_timezone:
        try:
            tz = pytz.timezone(user_timezone)
            now = now.astimezone(tz)
        except:
            pass  # Fall back to server timezone
    
    # Get today's date in the appropriate timezone
    today = now.date()
    today_str = today.strftime("%Y-%m-%d")
    
    if today_str in self.check_in_days:
        return False  # Already checked in today
    
    # Rest of the method remains the same...
```

### 4. Update the DailyCheckInAPI to pass timezone

In `account/views/oj_additions.py`:

```python
class DailyCheckInAPI(APIView):
    """POST /api/user/daily-check-in/"""
    @login_required
    def post(self, request):
        user = request.user
        
        # Get timezone from request (frontend should send this)
        user_timezone = request.data.get('timezone', 'UTC')
        
        # Get today's date in user's timezone
        from django.utils import timezone
        import pytz
        
        try:
            tz = pytz.timezone(user_timezone)
            today = timezone.now().astimezone(tz).date()
        except:
            today = timezone.now().date()
        
        # Check if user has solved any problem today
        today_submissions = Submission.objects.filter(
            user_id=user.id,
            result=JudgeStatus.ACCEPTED,
            create_time__date=today
        ).exists()
        
        # ... rest of the method
```

## Quick Frontend-Only Fix

If you want a quick fix without changing the backend, update the frontend to handle UTC dates properly:

```javascript
// In DailyCheckIn.vue
checkedInToday() {
  if (!this.streakData.check_in_days || this.streakData.check_in_days.length === 0) {
    return false;
  }
  
  // Get today's date in UTC (to match backend storage)
  const todayUTC = moment.utc().format('YYYY-MM-DD');
  const todayLocal = moment().format('YYYY-MM-DD');
  
  // Check both UTC and local date (to handle timezone boundaries)
  return this.streakData.check_in_days.includes(todayUTC) || 
         this.streakData.check_in_days.includes(todayLocal);
}
```

## Testing the Fix

1. Clear any existing check-in data
2. Make a new check-in
3. Verify that:
   - The check-in shows as completed for today
   - The calendar highlights the correct date
   - The streak count is accurate

## Additional Considerations

- Consider storing the user's timezone preference in their profile
- Always display dates/times in the user's local timezone in the UI
- Use consistent date formatting throughout the application