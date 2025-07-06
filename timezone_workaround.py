#!/usr/bin/env python3
"""Workaround to fix timezone issues in existing check-ins"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj.settings')
django.setup()

from account.models import UserStreak, User
from datetime import datetime, timedelta

def fix_checkin_dates():
    """Fix check-in dates for PDT users"""
    
    # Get all user streaks
    streaks = UserStreak.objects.all()
    
    for streak in streaks:
        print(f"\nUser: {streak.user.username}")
        print(f"Current check_in_days: {streak.check_in_days}")
        
        # Create a new list with both UTC and PDT dates
        updated_days = []
        for date_str in streak.check_in_days:
            updated_days.append(date_str)
            
            # Parse the date
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # Add the previous day (for PDT timezone)
            prev_day = date_obj - timedelta(days=1)
            prev_day_str = prev_day.strftime("%Y-%m-%d")
            
            if prev_day_str not in updated_days:
                updated_days.append(prev_day_str)
                print(f"  Adding PDT date: {prev_day_str} (for UTC date {date_str})")
        
        # Update the streak
        streak.check_in_days = sorted(updated_days)
        streak.save()
        print(f"Updated check_in_days: {streak.check_in_days}")
        
        # Also fix the last_check_in date if needed
        if streak.last_check_in:
            # Subtract 7 hours for PDT
            pdt_time = streak.last_check_in - timedelta(hours=7)
            print(f"Last check-in UTC: {streak.last_check_in}")
            print(f"Last check-in PDT: {pdt_time}")


if __name__ == "__main__":
    print("Fixing timezone issues in check-in dates...")
    fix_checkin_dates()
    print("\nDone!")