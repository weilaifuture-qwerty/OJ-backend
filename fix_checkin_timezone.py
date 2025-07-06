#!/usr/bin/env python3
"""Debug script to test timezone handling in check-in"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oj.settings')
django.setup()

from django.utils import timezone
from account.models import UserStreak, User

# Test timezone conversion
print("Testing timezone conversion...")
print(f"Current UTC time: {timezone.now()}")

# Simulate PDT timezone offset (420 minutes)
timezone_offset = 420  # PDT is UTC-7, so offset is positive 420
user_offset = timedelta(minutes=-timezone_offset)
utc_now = timezone.now()
user_now = utc_now + user_offset

print(f"User's local time: {user_now}")
print(f"UTC date: {utc_now.date()}")
print(f"User's local date: {user_now.date()}")

# Test with a specific time that crosses date boundary
# July 5, 2025, 5:35 PM PDT = July 6, 2025, 12:35 AM UTC
test_utc = datetime(2025, 7, 6, 0, 35, 0).replace(tzinfo=timezone.utc)
test_local = test_utc + user_offset
print(f"\nTest case:")
print(f"UTC time: {test_utc} (date: {test_utc.date()})")
print(f"Local time: {test_local} (date: {test_local.date()})")

# Show what should be stored
print(f"\nFor check-in at 5:35 PM PDT on July 5:")
print(f"Should store date as: {test_local.date().strftime('%Y-%m-%d')}")
print(f"Currently storing as: {test_utc.date().strftime('%Y-%m-%d')}")