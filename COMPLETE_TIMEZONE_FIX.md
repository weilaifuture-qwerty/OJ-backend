# Complete Timezone Fix for Daily Check-in

## Frontend Changes

### 1. Update the API call to include timezone offset

In your `api.js` or wherever the `dailyCheckIn` method is defined:

```javascript
dailyCheckIn() {
  console.log('[API DEBUG] dailyCheckIn called with timezone offset:', new Date().getTimezoneOffset());
  return request({
    url: 'daily_check_in',
    method: 'post',
    data: {
      timezone_offset: new Date().getTimezoneOffset()
    }
  });
}
```

### 2. Update DailyCheckIn.vue computed property

```javascript
checkedInToday() {
  if (!this.streakData.check_in_days || this.streakData.check_in_days.length === 0) {
    return false;
  }
  
  // Get today's date in local timezone
  const today = moment().format('YYYY-MM-DD');
  
  console.log('[DEBUG] checkedInToday:', {
    today: today,
    check_in_days: this.streakData.check_in_days,
    includes_today: this.streakData.check_in_days.includes(today)
  });
  
  // Check if today is in the check_in_days array
  return this.streakData.check_in_days.includes(today);
}
```

## Backend Fix (Already Applied)

The backend has been updated to:
1. Accept `timezone_offset` from the request
2. Calculate the user's local date
3. Store check-ins using the user's local date

## Quick Test

To verify the fix is working:

1. Check the current data:
```python
# Django shell
from account.models import UserStreak
streak = UserStreak.objects.first()
print(f"Check-in days: {streak.check_in_days}")
```

2. Clear the test data and try again:
```python
# Clear existing check-ins
streak.check_in_days = []
streak.current_streak = 0
streak.save()
```

3. Make a new check-in and verify it uses the correct date

## Alternative Backend Fix

If the timezone offset isn't being sent properly, here's a simpler fix that stores both UTC and local dates:

```python
# In account/models.py
class UserStreak(models.Model):
    # ... existing fields ...
    check_in_days = JSONField(default=list)  # Stores local dates
    check_in_days_utc = JSONField(default=list)  # Stores UTC dates
    
    def check_in(self, user_date=None):
        """Record a daily check-in"""
        from django.utils import timezone
        
        # Get both UTC and local dates
        utc_today = timezone.now().date()
        utc_today_str = utc_today.strftime("%Y-%m-%d")
        
        # Use provided date or default to UTC today
        local_today = user_date if user_date else utc_today
        local_today_str = local_today.strftime("%Y-%m-%d")
        
        # Check both lists
        if local_today_str in self.check_in_days or utc_today_str in self.check_in_days_utc:
            return False  # Already checked in today
        
        # Add to both lists
        self.check_in_days.append(local_today_str)
        if utc_today_str not in self.check_in_days_utc:
            self.check_in_days_utc.append(utc_today_str)
        
        # Rest of the method...
```

## Debugging the Issue

Add this to your DailyCheckInAPI to see what's being received:

```python
def post(self, request):
    # Debug logging
    print(f"[DEBUG] Check-in request data: {request.data}")
    print(f"[DEBUG] Timezone offset received: {request.data.get('timezone_offset', 'NOT SENT')}")
    
    # ... rest of the method
```

This will help identify if the timezone_offset is being sent from the frontend.